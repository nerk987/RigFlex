# RigFlex - Simple Soft Body for Armatures

# 1.0 Introduction
The movement of many animated characters is improved by some sort of soft body simulation. Antennas, clothing, tails, feathers, scales - you name it. Blender has a variety of techniques for this, often using soft body or cloth simulation applied to a lattice or mesh which in turn is applied to the cahracter mesh via modifiers. It's very flexible and powerful, but take some effort to set up.

However, there is no soft body for armatures, and often an acurate simulation is not the goal, just a simple first order lag to the movement of some of the mesh. The RigFlex addon aims to make this a simple process. 

#2.0 Installation

Download the RigFlex.zip file, install and enable in the usual way.

#3.0 Usage

##3.1 Quick Start

Briefly, you animate your rig however you want. When your're done, in Pose mode, select the deform bones that require a 'soft body' action. Locate the RigFlex2 tab in the Toolshelf to the left. In the 'Initial Setup' panel, click on the 'Initialze' button. The bones you had selected are duplicated to the bone layer shown in the same panel, and any meshes which have an assocoiated armature modifier or parent are updated to those bones if required. Then in the 'Main' panel, set the start and end frames to be baked, and press the 'Bake' button.

The addon adds keyframes for the bones you originally selected over the start to end frames. These bones should now have a soft body look. 

To change the animation, click on the 'Free Bake' button and the new bones will be track the original bones. Modify the animation on the original rig, then hit the 'Bake' button again. Once again the soft body action will be baked to the new bone layer.

The armature and associated meshes can be returned to their original state is you want to start over, or just want to remove the effects of the addon. Use the 'Revert' button in the 'Removal' panel.

##3.2 Changing the 'Stiffness'
The soft body algorithm for this addon is purposely kept very simple, and acts as a heavily damped spring system. A stiffness of 1.0 will result in an exact copy. With a stiffness of 0.5, the simulated bone will move around halfway towards the original bone's location each scan. A stiffness of 0.1 will be very floppy. There should be no overshoot unless movements are very extreme.

When the soft body layer is first initialized, each new deform bone is assigned a 'Stiffness' to a custom bone property. The deform bones are assigned a stiffness  based on the stiffness property (0.5 by default). This can be adjusted using the 'Update' button in the update panel. Select the bones you want to change from the soft body bone layer (not the orginal bones), set the required stiffness, and click on 'Update'. You can repeat this as often as you need.  The stiffness value can also be changed directly in the custom properties area of the bone tab.

When you're done, click on the bake button. 

##3.3 Rigify and 'medium complexity' rigs
This addon was intended to provide a simple soft body feel to a few bones in a chain. It may by possible to use it for more wide ranging purposes, but there are a few issues. In many rigs - such as rigify - when only the deform bones are retained in the 'sim' rig, some parenting information is lost. For example the upper arm deform bone is unlikely to be parented directly to a spine bone (this is done via organisational bones). In this case if both the spine and the arm bones are given a stiffness less than 1.0, things won't work right because the arm bone in the sim rig will copy the location of the arm bone in the original rig rather than following the soft body motion of the spine. As a work around, you can manually parent the arm bone in the sim rig to the shoulder/spine bone in the sim rig, etc, etc. Then bake again and it may do what you want!

##3.4 Blenrig and 'high complexity' rig
Blenrig now has more than 2000 deform bones, and the RigFlex addon doesn't work with it. However it's liekly that you want the soft body feel on auxialiary things - rabbit ears or radio antennae, hair or a cape. It's better to just make a new armature for those things, and parent or copy transforms to the appropriate bones in the original rig. Then run RigFlex on this simple additional rig.

