import os
import unittest
import logging
import vtk, qt, ctk, slicer, numpy
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# StudyAdmin 
#

class StudyAdmin(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "StudyAdmin"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Research"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = [""]  # TODO: replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
"""  # TODO: update with short description of the module
    self.parent.helpText += self.getDefaultModuleDocumentationLink()  # TODO: verify that the default URL is correct or change it to the actual documentation
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""  # TODO: replace with organization, grant and thanks.

#
# StudyAdminWidget
#

class StudyAdminWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None


  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/StudyAdmin.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create a new parameterNode
    # This parameterNode stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.
    self.logic = StudyAdminLogic()  

    self.studyAdminToolbar = slicer.util.mainWindow().addToolBar('StudyAdmin')
    self.patientSelectionComboBox = slicer.qMRMLSubjectHierarchyComboBox()
    self.patientSelectionComboBox.setMRMLScene(slicer.mrmlScene)
    self.patientSelectionComboBox.setAttributeFilter('Level', 'Patient')
    self.prevPatientToolbarButton = qt.QPushButton("Prev pat")
    self.nextPatientToolbarButton = qt.QPushButton("Next pat")
    self.studyAdminToolbar.addWidget(self.patientSelectionComboBox)
    self.studyAdminToolbar.addWidget(self.prevPatientToolbarButton)
    self.studyAdminToolbar.addWidget(self.nextPatientToolbarButton)

    self.setParameterNode(self.logic.getParameterNode())

    self.ui.patientTreeView.connect("currentItemChanged(vtkIdType)", self.logic.setPatient)
    self.ui.registerButton.connect("pressed()", self.logic.elastixRegister)
    self.patientSelectionComboBox.connect("currentItemChanged(vtkIdType)", self.logic.setPatient)
    self.prevPatientToolbarButton.connect("pressed()", self.logic.prevPatient)
    self.nextPatientToolbarButton.connect("pressed()", self.logic.nextPatient)

    self.customLayoutId = 1031
  

    layout = """
    <layout type="vertical" split="true">
      <item>
        <layout type="horizontal" split="true">
          <item splitSize="500">
            <view class="vtkMRMLSliceNode" singletontag="Red">
              <property name="orientation" action="default">Axial</property>
              <property name="viewlabel" action="default">R</property>
              <property name="viewcolor" action="default">#F34A33</property>
            </view>
          </item>
          <item splitSize="500">
            <view class="vtkMRMLSliceNode" singletontag="Diffusion">
              <property name="orientation" action="default">Axial</property>
              <property name="viewlabel" action="default">D</property>
              <property name="viewcolor" action="default">#EDD54C</property>
            </view>
          </item>
        </layout>
      </item>
      <item>
        <layout type="horizontal" split="true">
          <item splitSize="500">
            <view class="vtkMRMLSliceNode" singletontag="Green">
              <property name="orientation" action="default">Axial</property>
              <property name="viewlabel" action="default">G</property>
              <property name="viewcolor" action="default">#F34A32</property>
            </view>
          </item>
          <item splitSize="500">
            <view class="vtkMRMLSliceNode" singletontag="Yellow">
              <property name="orientation" action="default">Axial</property>
              <property name="viewlabel" action="default">Y</property>
              <property name="viewcolor" action="default">#EDD54D</property>
            </view>
          </item>
        </layout>
      </item>
    </layout>
    """

    layoutManager = slicer.app.layoutManager()
    layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(self.customLayoutId, layout)
    # Initial GUI update
    self.updateGUIFromParameterNode()

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def setParameterNode(self, inputParameterNode):
    """
    Adds observers to the selected parameter node. Observation is needed because when the
    parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    if inputParameterNode == self._parameterNode:
      # No change
      return

    # Unobserve previusly selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    if inputParameterNode is not None:
      self.addObserver(inputParameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def getCompositeNode(self, layoutName):
    count = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceCompositeNode')

    for n in range(count):
      compNode = slicer.mrmlScene.GetNthNodeByClass(n, 'vtkMRMLSliceCompositeNode')
      if layoutName and compNode.GetLayoutName() != layoutName:
        continue
      return compNode

  def setDefaultMasterVolumeNodeID(self, backgroundID, diffusionVolumeID, segmentationNodeID, adcNodeID):
    compositeNode = self.getCompositeNode('Red')
    compositeNode.SetBackgroundVolumeID(backgroundID)
    compositeNode.SetLinkedControl(True)
    layoutManager = slicer.app.layoutManager()
    layoutManager.sliceWidget('Red').findChild(slicer.qMRMLSegmentSelectorWidget).setCurrentNodeID(logic.getNode('segmentation').GetID()) #segmentationNodeID)
    self.getCompositeNode('Diffusion').SetBackgroundVolumeID(logic.getNode('b800').GetID()) #diffusionVolumeID)
    self.getCompositeNode('Diffusion').SetLinkedControl(True)
    backgroundNode = slicer.mrmlScene.GetNodeByID(backgroundID)
    layoutManager.sliceWidget('Red').mrmlSliceNode().RotateToVolumePlane(backgroundNode)
    layoutManager.sliceWidget('Diffusion').mrmlSliceNode().RotateToVolumePlane(backgroundNode)

    self.getCompositeNode('Yellow').SetBackgroundVolumeID(logic.getNode('adc').GetID())
    self.getCompositeNode('Green').SetBackgroundVolumeID(logic.getNode('b800').GetID())
    layoutManager.sliceWidget('Yellow').mrmlSliceNode().RotateToVolumePlane(backgroundNode)
    layoutManager.sliceWidget('Green').mrmlSliceNode().RotateToVolumePlane(backgroundNode)
    self.getCompositeNode('Yellow').SetLinkedControl(True)
    self.getCompositeNode('Green').SetLinkedControl(True)

  def setPatientSegmentationsVisible(self, patientSHIndex):
    numOfSegmentationNodes = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSegmentationNode')
    for i in range(numOfSegmentationNodes):
      segNode = slicer.mrmlScene.GetNthNodeByClass(i, 'vtkMRMLSegmentationNode')
      shId = shNode.GetItemByDataNode(segNode)
      if segNode.GetDisplayNode():
        segNode.GetDisplayNode().SetVisibility(self.patientIndex(shId) == newPatientIndex)

  def setPatient(self, hierarchyIndex):
    if not (self.logic.setPatient(self.logic.patientIndex(hierarchyIndex))):
      return

    self.updateGUIFromParameterNode()
    
    self.setDefaultMasterVolumeNodeID(selectedVolume.GetID(), diffusionVolume.GetID(), patientsSegmentation.GetID(), adcNode.GetID())

    self.setPatientSegmentationsVisible(newPatientIndex)

    layoutManager = slicer.app.layoutManager()
    #layoutManager.sliceWidget('Diffusion').sliceLogic().FitSliceToAll()
    #fov = layoutManager.sliceWidget('Diffusion').sliceController().mrmlSliceNode().GetFieldOfView()
    #layoutManager.sliceWidget('Red').sliceController().setSliceFOV(min(fov[0], fov[1]))
    slicer.app.layoutManager().sliceWidget('Red').sliceController().setSliceFOV(300)
    layoutManager.sliceWidget('Diffusion').sliceController().setSliceFOV(300)


  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    slicer.app.layoutManager().setLayout(1031)

    # Disable all sections if no parameter node is selected
    if self._parameterNode is None:
      return

    # Update each widget from parameter node
    # Need to temporarily block signals to prevent infinite recursion (MRML node update triggers
    # GUI update, which triggers MRML node update, which triggers GUI update, ...)

    wasBlocked = self.ui.patientTreeView.blockSignals(True)
    self.ui.patientTreeView.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
    self.ui.patientTreeView.blockSignals(wasBlocked)

    wasBlocked = self.patientSelectionComboBox.blockSignals(True)
    self.patientSelectionComboBox.setCurrentItem(int(self._parameterNode.GetParameter("PatientIndex")))
    self.patientSelectionComboBox.blockSignals(wasBlocked)

    #wasBlocked = slicer.modules.SegmentEditorWidget.editor.blockSignals(True)  
    segmentationNodeId = str(self._parameterNode.GetNodeReferenceID("SegmentationNode"))
    if segmentationNodeId != "" and hasattr(slicer.modules, 'SegmentEditorWidget'):
      slicer.modules.SegmentEditorWidget.editor.setSegmentationNodeID(segmentationNodeId)
    #slicer.modules.SegmentEditorWidget.editor.blockSignals(wasBlocked)
#
# StudyAdminLogic
#

class StudyAdminLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    parameterNode.SetParameter("PatientIndex", '-1')
 
  def run(self, inputVolume, outputVolume):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
     """

    if not inputVolume or not outputVolume:
      raise ValueError("Input or output volume is invalid")

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {
      'InputVolume': inputVolume.GetID(),
      'OutputVolume': outputVolume.GetID(),
      'ThresholdValue' : 50,
      'ThresholdType' : 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=True)

    logging.info('Processing completed')

  def findSeries(self, studySHIndex, id, nameSearch, nameSearch2='', nodeType='vtkMRMLScalarVolumeNode'):
    seriesIds = vtk.vtkIdList()
    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    shNode.GetItemChildren(studySHIndex, seriesIds)
    for i in range(seriesIds.GetNumberOfIds()):
      seriesId = seriesIds.GetId(i)
      dataNode = shNode.GetItemDataNode(seriesId)
      if dataNode is not None:
        name = dataNode.GetName()
        if dataNode.GetClassName() == nodeType and nameSearch in name and nameSearch2 in name:
          self.getParameterNode().SetNodeReferenceID(id, dataNode.GetID())
          return dataNode
    return None

  def getNode(self, name):
    return self.getParameterNode().GetNodeReference(name)

  def getOrCreateNode(self, name, className = "vtkMRMLScalarVolumeNode"):
    node = self.getNode(name)
    if node is None:
      node = slicer.mrmlScene.AddNewNodeByClass(className, name)
      if className == 'vtkMRMLSegmentationNode':
        node.CreateDefaultDisplayNodes()
      shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
      shItemID = shNode.GetItemByDataNode(node)
      shNode.SetItemParent(shItemID, int(self.getParameterNode().GetParameter("StudyIndex")))
      self.getParameterNode().SetNodeReferenceID(name, node.GetID())
    return node

  def patientIndex(self, hierarchyIndex):
    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    if shNode.GetItemLevel(hierarchyIndex) == 'Patient':
      return hierarchyIndex
    else:
      return shNode.GetItemAncestorAtLevel(hierarchyIndex, 'Patient')

  def currentPatientIndex(self):
    patientIndex = self.getParameterNode().GetParameter("PatientIndex")
    if patientIndex is None or str(patientIndex) == '':
      return -1
    return int(patientIndex)

  def nextPatient(self):
    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    patientIndex = self.currentPatientIndex()
    if patientIndex == -1:
      return
    pos = shNode.GetItemPositionUnderParent(patientIndex)
    parent = shNode.GetItemParent(patientIndex)
    if shNode.GetNumberOfItemChildren(parent) > pos + 1:
      self.setPatient(shNode.GetItemByPositionUnderParent(parent, pos + 1))

  def prevPatient(self):
    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    patientIndex = self.currentPatientIndex()
    if patientIndex == -1:
      return
    pos = shNode.GetItemPositionUnderParent(patientIndex)
    parent = shNode.GetItemParent(patientIndex)
    if pos > 0:
      self.setPatient(shNode.GetItemByPositionUnderParent(parent, pos - 1))

  def setPatient(self, patientSHIndex):
    parameterNode = self.getParameterNode()

    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
    newPatientIndex = self.patientIndex(patientSHIndex)
    if self.currentPatientIndex() == newPatientIndex:
      return False
    parameterNode.SetParameter("PatientIndex", str(newPatientIndex))

    studyIds = vtk.vtkIdList()
    shNode.GetItemChildren(newPatientIndex, studyIds)
    if studyIds.GetNumberOfIds() <= 0:
      return False
    studyId = studyIds.GetId(0)
    parameterNode.SetParameter("StudyIndex", str(studyId))
    if not (self.findSeries(studyId, 't2', 'T2W', nameSearch2='tra') and self.findSeries(studyId, 'adc', 'ADC') and self.findSeries(studyId, 'b800', 'b 800')):
      return False
    if not self.findSeries(studyId, 'b0', 'b0'):
      calculatedB0 = self.virtualB0Calc(self.getNode("adc"), self.getNode('b800'), self.getNode('t2'))
    if not self.findSeries(studyId, 'segmentation', 'segmentation', nodeType='vtkMRMLSegmentationNode'):
      segmentationNode = self.getOrCreateNode('segmentation', className = 'vtkMRMLSegmentationNode')
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.getNode('t2'))
      lymphNodeSeg = slicer.vtkSegment()
      lymphNodeSeg.SetName('Lymph node')
      lymphNodeSeg.SetColor(0.2, 0.9, 0.1)
      segmentationNode.GetSegmentation().AddSegment(lymphNodeSeg)
    
    return True

  def resizeVolume(self, sourceNode, targetNode, name):
    resultNode = self.getOrCreateNode(name)

    parameters = {
      'inputVolume' : sourceNode.GetID(),
      'referenceVolume' : targetNode.GetID(),
      'outputVolume' : resultNode.GetID()
    }
    cliNode = slicer.cli.runSync(slicer.modules.resamplescalarvectordwivolume, None, parameters, update_display=False)
    return resultNode

  def transformVolume(self, sourceNode, targetNode, transformNode, name):
    resultNode = self.getOrCreateNode(name)

    parameters = {
      'inputVolume' : sourceNode.GetID(),
      'referenceVolume' : targetNode.GetID(),
      'outputVolume' : resultNode.GetID(),
      'transformationFile' : transformNode.GetID()
    }
    cliNode = slicer.cli.runSync(slicer.modules.resamplescalarvectordwivolume, None, parameters, update_display=False)
    return resultNode



  def thresholdFilter(sourceNode, min, max):
    filter = vtk.vtkImageThreshold()
    filter.ThresholdBetween(min, max)
    filter.SetInputData(sourceNode.GetImageData())
    filter.SetInValue(1)
    filter.SetOutValue(0)
    return filter

  def addFilters(sourceFilterA, sourceFilterB):
    filter = vtk.vtkImageMathematics()
    filter.SetOperationToAdd()
    filter.AddInputConnection(0, sourceFilterA.GetOutputPort())
    filter.AddInputConnection(1, sourceFilterB.GetOutputPort())
    return filter

  def thresholdVolume(self, sourceNode, name, m, min, max):
    filter = vtk.vtkImageThreshold()
    filter.ThresholdBetween(min, max)
    filter.SetInputData(sourceNode.GetImageData())
    filter.SetInValue(1)
    filter.SetOutValue(0)
    filter.Update()
    resultNode = self.getOrCreateNode(name)
    resultNode.SetIJKToRASMatrix(m)
    resultNode.SetImageDataConnection(filter.GetOutputPort())
    return resultNode

  def volumeToSegmentationNode(self, sourceNode, name, segmentName):
    orientedData = slicer.vtkOrientedImageData()
    orientedData.ShallowCopy(sourceNode.GetImageData())
    m2 = vtk.vtkMatrix4x4()
    sourceNode.GetIJKToRASDirectionMatrix(m2)
    orientedData.SetDirectionMatrix(m2)
    orientedData.SetOrigin(sourceNode.GetOrigin())
    orientedData.SetSpacing(sourceNode.GetSpacing())
    resultSegmentationNode = self.getOrCreateNode(name, 'vtkMRMLSegmentationNode')
    resultSegmentationNode.CreateDefaultDisplayNodes()
    resultSegmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(sourceNode)
    resultSegmentationNode.RemoveSegment(segmentName)
    resultSegmentationNode.AddSegmentFromBinaryLabelmapRepresentation(orientedData, segmentName)
    return resultSegmentationNode

  def volumeAndVolume(self, sourceNode1, sourceNode2, name):
    m = vtk.vtkMatrix4x4()
    sourceNode1.GetIJKToRASMatrix(m)
    imageLogicFilter = vtk.vtkImageLogic()
    imageLogicFilter.SetOperationToAnd()
    imageLogicFilter.SetInput1Data(sourceNode1.GetImageData())
    imageLogicFilter.SetInput2Data(sourceNode2.GetImageData())
    imageLogicFilter.SetOutputTrueValue(1)
    imageLogicFilter.Update()
    resultNode = self.getOrCreateNode(name)
    resultNode.SetImageDataConnection(imageLogicFilter.GetOutputPort())
    resultNode.SetIJKToRASMatrix(m)
    return resultNode

  def virtualB0Calc(self, adcNode, b800Node, t2Node):
    m = vtk.vtkMatrix4x4()
    t2Node.GetIJKToRASMatrix(m)
    resizedB800Node = self.resizeVolume(b800Node, t2Node, 'Resized b800')    
    resizedAdcNode = self.resizeVolume(adcNode, t2Node, 'Resized ADC')
    b800Arr = slicer.util.arrayFromVolume(resizedB800Node)
    ADCArr = slicer.util.arrayFromVolume(resizedAdcNode) / 1000000
    b0Arr = b800Arr*numpy.exp(800 * ADCArr)
    b0 = self.getOrCreateNode('b0')
    b0.SetIJKToRASMatrix(m)
    slicer.util.updateVolumeFromArray(b0, b0Arr)
    return b0

  def virtualB0(self):
    parameterNode = self.getParameterNode()
    adcNode = parameterNode.GetNodeReference("adc")
    b800Node = parameterNode.GetNodeReference("b800")
    t2Node = parameterNode.GetNodeReference("t2")
    if t2Node is None:
      return
    b0Node = self.virtualB0Calc(adcNode, b800Node, t2Node)
    parameterNode.SetNodeReferenceID("b0", b0Node.GetID())

  def elastixRegister(self):
    parameterNode = self.getParameterNode()
    t2Node = parameterNode.GetNodeReference("t2")
    b0Node = parameterNode.GetNodeReference("b0")
    if b0Node is None:
      self.virtualB0()
      b0Node = parameterNode.GetNodeReference("b0")
      if b0Node is None:
        return

    b0RegNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    b0RegNode.SetName('b0 reg')
    b0TransformNode = self.getOrCreateNode('b0 transform', "vtkMRMLTransformNode")

    slicer.modules.ElastixWidget.logic.registerVolumes(t2Node, b0Node,
      ['Rigid.txt', 'Deformable.txt'],
      outputVolumeNode = b0RegNode,
      outputTransformNode = b0TransformNode)

    adcReg = self.transformVolume(parameterNode.GetNodeReference("adc"), t2Node, b0TransformNode, 'ADC reg')
    b800Reg = self.transformVolume(parameterNode.GetNodeReference("b800"), t2Node, b0TransformNode, 'b800 reg')

    parameterNode.SetNodeReferenceID("adc reg", adcReg.GetID())
    parameterNode.SetNodeReferenceID("b800 reg", b800Reg.GetID())



  def segmentTumor(self, adcNode, b800Node, t2Node, t2Min=115, t2Max=260, b800Min=100, b800Max=450, adcMin=600, adcMax=1700):
    m = vtk.vtkMatrix4x4()
    t2Node.GetIJKToRASMatrix(m)

    segName = 'Comp segmentation'
    t2SegNode = self.thresholdVolume(t2Node, 'T2 segmentation', m, t2Min, t2Max)
    t2SegmentationNode = self.volumeToSegmentationNode(t2SegNode, segName, 'T2_Segmentation')
    
    b800SegNode = self.thresholdVolume(b800Node, 'b800 segmentation', m, b800Min, b800Max)
    b800SegmentationNode = self.volumeToSegmentationNode(b800SegNode, segName, 'b800_Segmentation')
    
    adcSegNode = self.thresholdVolume(adcNode, 'Segmented ADC', m, adcMin, adcMax)
    adcSegmentationNode = self.volumeToSegmentationNode(adcSegNode, segName, 'ADC_Segmentation')

    comb1Node = self.volumeAndVolume(t2SegNode, b800SegNode, 'Comb segmented')
    comb1Node = self.volumeAndVolume(comb1Node, adcSegNode, 'All comb segmented')
    combSegmentationNode = self.volumeToSegmentationNode(comb1Node, segName, 'All comb Segmentation')

  def segment(self, t2Min=115, t2Max=260, b800Min=100, b800Max=450, adcMin=600, adcMax=1700):
    parameterNode = self.getParameterNode()
    adcNode = node = slicer.mrmlScene.GetFirstNodeByName('ADC reg')
    b800Node = node = slicer.mrmlScene.GetFirstNodeByName('b800 reg')
    t2Node = parameterNode.GetNodeReference("t2")

    self.segmentTumor(adcNode, b800Node, t2Node, t2Min, t2Max, b800Min, b800Max, adcMin, adcMax)

#
# StudyAdminTest
#

class StudyAdminTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_StudyAdmin1()

  def test_StudyAdmin1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    inputVolume = SampleData.downloadFromURL(
      nodeNames='MRHead',
      fileNames='MR-Head.nrrd',
      uris='https://github.com/Slicer/SlicerTestingData/releases/download/MD5/39b01631b7b38232a220007230624c8e',
      checksums='MD5:39b01631b7b38232a220007230624c8e')[0]
    self.delayDisplay('Finished with download and loading')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 279)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")

    # Test the module logic

    logic = StudyAdminLogic()

    # Test algorithm with non-inverted threshold
    logic.run(inputVolume, outputVolume)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], 50)

    self.delayDisplay('Test passed')
