import maya.cmds as cmds

WINDOW_NAME = "LightBlockerConnectorWindow"
WINDOW_TITLE = "aiLightBlocker Connector"

def pick_light_blocker(*args):
    """
    Stores the selected node as the 'Light Blocker' in the textField.
    """
    selection = cmds.ls(sl=True)
    if not selection:
        cmds.warning("No objects selected to set as Light Blocker.")
        return
    
    # We simply assume the first selected object is the blocker
    blocker = selection[0]
    cmds.textField("lightBlockerField", e=True, tx=blocker)

def add_selected_lights(*args):
    """
    Add the selected lights to the textScrollList for Lights.
    """
    selection = cmds.ls(sl=True)
    if not selection:
        cmds.warning("No lights selected to add.")
        return
    
    for obj in selection:
        # Skip duplicates in the list
        existing = cmds.textScrollList("lightListTSL", q=True, ai=True) or []
        if obj not in existing:
            cmds.textScrollList("lightListTSL", e=True, a=obj)

def remove_selected_lights(*args):
    """
    Remove the selected items from the textScrollList for Lights.
    """
    selected_in_list = cmds.textScrollList("lightListTSL", q=True, si=True)
    if not selected_in_list:
        cmds.warning("No lights selected in the list to remove.")
        return
    for item in selected_in_list:
        cmds.textScrollList("lightListTSL", e=True, ri=item)

def connect_blocker(*args):
    """
    Connects the Light Blocker (message) to each selected light's aiFilters multi attribute.
    Finds the next available index if needed.
    """
    blocker = cmds.textField("lightBlockerField", q=True, tx=True)
    if not blocker or not cmds.objExists(blocker):
        cmds.warning("Invalid or no Light Blocker specified.")
        return
    
    lights = cmds.textScrollList("lightListTSL", q=True, ai=True)
    if not lights:
        cmds.warning("No lights in the list to connect.")
        return
    
    for light_transform in lights:
        # Get the shape of the light
        shapes = cmds.listRelatives(light_transform, s=True, f=True) or []
        if not shapes:
            cmds.warning("No shape found under '%s'. Skipping..." % light_transform)
            continue
        light_shape = shapes[0]
        
        # The attribute we need to connect to is "aiFilters", a multi-attribute.
        # We find the next available index
        multi_attr = light_shape + ".aiFilters"
        current_indices = cmds.getAttr(multi_attr, multiIndices=True)
        
        # Find the next available index
        next_index = 0
        if current_indices:
            # just find the first integer from 0..some range not in current_indices
            for idx in range(1000):
                if idx not in current_indices:
                    next_index = idx
                    break
        
        # Build the full attribute name for the next index
        dest_attr = f"{light_shape}.aiFilters[{next_index}]"
        
        # Connect
        try:
            cmds.connectAttr(blocker + ".message", dest_attr, f=True)
            print(f"Connected {blocker}.message -> {dest_attr}")
        except Exception as e:
            cmds.warning(f"Could not connect {blocker}.message -> {dest_attr}: {e}")

def disconnect_blocker(*args):
    """
    Disconnects the currently set Light Blocker from any aiFilters connection
    on the lights in the list.
    """
    blocker = cmds.textField("lightBlockerField", q=True, tx=True)
    if not blocker or not cmds.objExists(blocker):
        cmds.warning("Invalid or no Light Blocker specified.")
        return
    
    lights = cmds.textScrollList("lightListTSL", q=True, ai=True)
    if not lights:
        cmds.warning("No lights in the list to disconnect.")
        return
    
    for light_transform in lights:
        shapes = cmds.listRelatives(light_transform, s=True, f=True) or []
        if not shapes:
            cmds.warning("No shape found under '%s'. Skipping..." % light_transform)
            continue
        light_shape = shapes[0]
        
        # Find all connections to the shape's aiFilters multi
        connections = cmds.listConnections(light_shape + ".aiFilters", 
                                           plugs=True, 
                                           connections=True) or []
        # listConnections with `connections=True` returns pairs: [destAttr, sourceAttr, destAttr, sourceAttr, ...]
        # We want to break the ones where source = blocker.message
        # or where dest = shape.aiFilters[..] referencing the same blocker.
        
        # We'll parse in pairs
        for i in range(0, len(connections), 2):
            dest_plug = connections[i]
            src_plug = connections[i+1]
            
            # We want: src_plug == "myBlocker.message" and dest_plug contains "lightShape.aiFilters[...]"
            # The order of pairs can vary, so let's check both ways
            if (blocker + ".message" == src_plug) and (".aiFilters[" in dest_plug):
                # This is the connection we want to break
                try:
                    cmds.disconnectAttr(src_plug, dest_plug)
                    print(f"Disconnected {src_plug} -> {dest_plug}")
                except Exception as e:
                    cmds.warning(f"Could not disconnect {src_plug} -> {dest_plug}: {e}")

def build_ui():
    """
    Build the UI window.
    """
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)
    
    cmds.window(WINDOW_NAME, t=WINDOW_TITLE, s=False, mnb=False, mxb=False)
    cmds.columnLayout(adj=True, rs=5)
    
    # Pick Light Blocker row
    cmds.rowLayout(nc=2, adjustableColumn=1, columnAttach=[(1, 'right', 5)])
    cmds.text(label="Light Blocker:")
    cmds.setParent('..')
    
    cmds.rowLayout(nc=3, adjustableColumn=2, columnWidth3=[100,150,80], columnAlign=(1,'right'))
    cmds.textField("lightBlockerField", text="", editable=False)
    cmds.button(label="Pick Selected", c=pick_light_blocker)
    cmds.setParent('..')
    
    # Light list
    cmds.text(label="Lights in List:")
    cmds.textScrollList("lightListTSL", allowMultiSelection=True, h=120)
    
    cmds.rowLayout(nc=2, adjustableColumn=1)
    cmds.button(label="Add Selected Lights", c=add_selected_lights)
    cmds.button(label="Remove Selected", c=remove_selected_lights)
    cmds.setParent('..')
    
    # Connect / Disconnect Buttons
    cmds.separator(h=10, style='none')
    cmds.rowLayout(nc=2, adjustableColumn=1)
    cmds.button(label="Connect", bgc=(0.6, 0.8, 0.6), c=connect_blocker)
    cmds.button(label="Disconnect", bgc=(0.8, 0.6, 0.6), c=disconnect_blocker)
    cmds.setParent('..')
    
    cmds.separator(h=10, style='none')
    cmds.button(label="Close", c=lambda *args: cmds.deleteUI(WINDOW_NAME))
    
    cmds.setParent('..')
    cmds.window(WINDOW_NAME, e=True, w=300, h=200)
    cmds.showWindow(WINDOW_NAME)

# Run the UI
build_ui()
