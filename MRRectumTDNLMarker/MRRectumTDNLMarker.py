import os
import os.path
import unittest
import logging
import vtk, qt, ctk, slicer, numpy
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# MRRectumTDNLMarker 
#

class MRRectumTDNLMarker(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "TDNL Marker"  # TODO: make this more human readable by adding spaces
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
# MRRectumTDNLMarkerWidget
#

class MRRectumTDNLMarkerWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/MRRectumTDNLMarker.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create a new parameterNode
    # This parameterNode stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.
    self.logic = MRRectumTDNLMarkerLogic()  

    self.tdnlMarkerToolbar = slicer.util.mainWindow().addToolBar('TDNLMarker')
    self.patientSelectionComboBox = slicer.qMRMLSubjectHierarchyComboBox()
    self.patientSelectionComboBox.setMRMLScene(slicer.mrmlScene)
    #self.patientSelectionComboBox.setAttributeFilter('Level', 'Patient')
    #self.prevPatientToolbarButton = qt.QPushButton("Prev pat")
    #self.nextPatientToolbarButton = qt.QPushButton("Next pat")
    #self.tdnlMarkerToolbar.addWidget(self.patientSelectionComboBox)
    #self.tdnlMarkerToolbar.addWidget(self.prevPatientToolbarButton)
    #self.tdnlMarkerToolbar.addWidget(self.nextPatientToolbarButton)

    self.setParameterNode(self.logic.getParameterNode())

    self.ui.patientTreeView.connect("currentItemChanged(vtkIdType)", self.logic.setPatient)
    self.ui.prevPatientButton.connect("pressed()", self.logic.prevPatient)
    self.ui.nextPatientButton.connect("pressed()", self.logic.nextPatient)
    self.ui.addTdButton.connect("pressed()", self.addTdMarker)
    self.ui.addLnButton.connect("pressed()", self.addLnMarker)
    self.ui.saveButton.connect("pressed()", self.logic.saveFiducials)
    #self.patientSelectionComboBox.connect("currentItemChanged(vtkIdType)", self.logic.setPatient)
    #self.prevPatientToolbarButton.connect("pressed()", self.logic.prevPatient)
    #self.nextPatientToolbarButton.connect("pressed()", self.logic.nextPatient)

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
            <view class="vtkMRMLSliceNode" singletontag="RU">
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
              <property name="orientation" action="default">Coronal</property>
              <property name="viewlabel" action="default">G</property>
              <property name="viewcolor" action="default">#F34A32</property>
            </view>
          </item>
          <item splitSize="500">
            <view class="vtkMRMLSliceNode" singletontag="Yellow">
              <property name="orientation" action="default">Sagittal</property>
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

  def showVolume(self, compositeNodeName, volumeName):
    compositeNode = self.getCompositeNode(compositeNodeName)
    volumeNode = self.logic.getNode(volumeName)
    compositeNode.SetBackgroundVolumeID(volumeNode.GetID())

    slicer.app.layoutManager().sliceWidget(compositeNodeName).mrmlSliceNode().RotateToVolumePlane(volumeNode)
    compositeNode.SetLinkedControl(True)

  def showVolumes(self):
    if self.logic.getParameterNode().GetParameter('PatientIndex') == '':
      return
    #layoutManager = slicer.app.layoutManager()
    #layoutManager.sliceWidget('Red').findChild(slicer.qMRMLSegmentSelectorWidget).setCurrentNodeID(logic.getNode('segmentation').GetID())
    
    self.showVolume('Red', 't2tra1')
    self.showVolume('RU', 't2tra2')
    self.showVolume('Green', 't2cor')
    self.showVolume('Yellow', 't2sag')

  #def setPatientSegmentationsVisible(self, patientSHIndex):
  #  numOfSegmentationNodes = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSegmentationNode')
  #  for i in range(numOfSegmentationNodes):
  #    segNode = slicer.mrmlScene.GetNthNodeByClass(i, 'vtkMRMLSegmentationNode')
  #    shId = shNode.GetItemByDataNode(segNode)
  #    if segNode.GetDisplayNode():
  #      segNode.GetDisplayNode().SetVisibility(self.patientIndex(shId) == newPatientIndex)

  def setPatient(self, hierarchyIndex):
    #if not (self.logic.setPatient(self.logic.patientIndex(hierarchyIndex))):
    return

    self.updateGUIFromParameterNode()
    
    self.showVolumes()

    #self.setPatientSegmentationsVisible(newPatientIndex)

    #layoutManager = slicer.app.layoutManager()
    #layoutManager.sliceWidget('Diffusion').sliceLogic().FitSliceToAll()
    #fov = layoutManager.sliceWidget('Diffusion').sliceController().mrmlSliceNode().GetFieldOfView()
    #layoutManager.sliceWidget('Red').sliceController().setSliceFOV(min(fov[0], fov[1]))
    #slicer.app.layoutManager().sliceWidget('Red').sliceController().setSliceFOV(300)
    #layoutManager.sliceWidget('Diffusion').sliceController().setSliceFOV(300)


  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """
    #logging.info('updateGUIFromParameterNode')

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
    #self.patientSelectionComboBox.setCurrentItem(int(self._parameterNode.GetParameter("PatientIndex")))
    self.patientSelectionComboBox.blockSignals(wasBlocked)

    #wasBlocked = slicer.modules.SegmentEditorWidget.editor.blockSignals(True)  
    segmentationNodeId = str(self._parameterNode.GetNodeReferenceID("SegmentationNode"))
    if segmentationNodeId != "" and hasattr(slicer.modules, 'SegmentEditorWidget'):
      slicer.modules.SegmentEditorWidget.editor.setSegmentationNodeID(segmentationNodeId)

    self.showVolumes()
    #slicer.modules.SegmentEditorWidget.editor.blockSignals(wasBlocked)
  
  def addTdMarker(self):
    self.addMarker('TD')

  def addLnMarker(self):
    self.addMarker('LN')

  def addMarker(self, fiducialNodeName):
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
    fiducialNode = self.logic.getNode(fiducialNodeName)
    selectionNode.SetActivePlaceNodeID(fiducialNode.GetID())
    interactionNode.SetCurrentInteractionMode(interactionNode.Place)
#
# MRRectumTDNLMarkerLogic
#

class MRRectumTDNLMarkerLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self):
    (self.baseDir, self.reviewer) = self.getInitInfo()
    (self.patientBaseDir, self.patientDirectories) = self.getPatientDirectories()
    (self.markupBaseDir, self.userMarkupDir, self.otherUsersMarkupDirs) = self.getMarkupDirectories()
    super().__init__()

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    self.patientIndex = -1
    parameterNode.SetParameter('PatientIndex', '')
 
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

  def getMarkupLabels(self):
    return ['TD', 'LN']

  def getInitInfo(self):
    locationFilePath = os.path.expanduser('~/tdnl.txt')
    if not os.path.isfile(locationFilePath):
      logging.error('Expected file tdnl.txt in home directory: ' + locationFilePath + 
        ' that is supposed to have two lines: One with the path to the directory containing data and ' +
        ' one with your name initials.')
      return ''
    
    locationFile = open(locationFilePath, 'r')
    baseDir = locationFile.readline().rstrip()
    if os.path.isdir(baseDir):
      logging.info('Base directory is ' + baseDir)
    else:
      logging.error('Base directory doen not exist: ' + baseDir)

    reviewer = locationFile.readline().rstrip()

    return (baseDir, reviewer)

  def getPatientDirectories(self):
    patientsDir = os.path.join(self.baseDir, 'patients')
    if os.path.isdir(patientsDir):
      patientDirectories = os.listdir(patientsDir)
      logging.info('Found patient directory with ' + str(patientDirectories.__len__()) + ' entries')
      return (patientsDir, [d for d in patientDirectories if os.path.isdir(os.path.join(patientsDir, d))])
    else:
      logging.error('Patients directory not found: ' + patientsDir)
    
    return ('', [])

  def getMarkupDirectories(self):
    markupBaseDir = os.path.join(self.baseDir, 'markup')
    if not os.path.isdir(markupBaseDir):
      os.makedirs(markupBaseDir)
    currentUser = self.getReviewer()
    userMarkupDir = os.path.join(markupBaseDir, currentUser)
    if not os.path.isdir(userMarkupDir):
      os.makedirs(userMarkupDir)
    otherUsersMarkupDirs = [d for d in os.listdir(markupBaseDir) if d != currentUser]
    logging.info('Markup directories, found ' + str(otherUsersMarkupDirs.__len__()) + ' others reviewers.')
    return (markupBaseDir, userMarkupDir, otherUsersMarkupDirs)

  def getReviewer(self):
    return self.reviewer

  def getFiducialFilePath(self, labelStr, user):
    return os.path.join(os.path.join(self.markupBaseDir, user, (self.currentPatientId() + '_' + labelStr)))

  def numberOfPatients(self):
    return self.patientDirectories.__len__()

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

  def currentPatientId(self):
    return self.getParameterNode().GetParameter('PatientId')

  def currentPatientIndex(self):
    return self.patientIndex

  def nextPatient(self):
    self.setPatient(self.currentPatientIndex() + 1)
  
  def prevPatient(self):
    self.setPatient(self.currentPatientIndex() - 1)

#[n.GetID() for n in slicer.mrmlScene.GetNodes() if n.GetSingletonTag() is None and 'Fiducial' in n.GetID()]

  def setPatient(self, newPatientIndex):
    logging.info('setPatient ' + str(newPatientIndex) + " current patient " + str(self.patientIndex))
    
    patientDirs = self.patientDirectories
    if newPatientIndex < 0 or newPatientIndex >= self.numberOfPatients() or self.currentPatientIndex() == newPatientIndex:
      return False

    slicer.mrmlScene.Clear(0)

    parameterNode = self.getParameterNode()
    parameterNode.SetParameter('PatientIndex', '')
    self.patientIndex = newPatientIndex
    patientId = patientDirs[newPatientIndex]

    patientPath = os.path.join(self.patientBaseDir, patientId)

    volumes = os.listdir(patientPath)

    for v in volumes:
      node = slicer.util.loadVolume(os.path.join(patientPath, v))
      parameterNode.SetNodeReferenceID(node.GetName(), node.GetID())
    
    parameterNode.SetParameter('PatientId', patientId)

    self.readFiducials()
    
    parameterNode.SetParameter('PatientIndex', str(self.patientIndex))
    return True

  def saveFiducials(self):
    for label in self.getMarkupLabels():
      fid = self.getNode(label)
      sn = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsJsonStorageNode") 
      sn.SetFileName(self.getFiducialFilePath(label))
      sn.WriteData(fid)
      slicer.mrmlScene.RemoveNode(sn)

  def readFiducials(self):
    self.readUserFiducials()
    self.readOtherUsersFiducials()

  def readUserFiducials(self):
    parameterNode = self.getParameterNode()
    for label in self.getMarkupLabels():
      fid = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", self.reviewer + '_' + label)
      sn = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsJsonStorageNode")
      path = self.getFiducialFilePath(label, self.reviewer)
      if os.path.isfile(path):
        sn.SetFileName(path)
        sn.ReadData(fid)
      parameterNode.SetNodeReferenceID(fid.GetName(), fid.GetID())
      slicer.mrmlScene.RemoveNode(sn)

  def readOtherUsersFiducials(self):
    parameterNode = self.getParameterNode()
    for otherUser in self.otherUsersMarkupDirs:
      for label in self.getMarkupLabels():
        fid = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", otherUser + '_' + label)
        sn = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsJsonStorageNode")
        path = self.getFiducialFilePath(label, otherUser)
        if os.path.isfile(path):
          sn.SetFileName(path)
          sn.ReadData(fid)
        parameterNode.SetNodeReferenceID(fid.GetName(), fid.GetID())
        slicer.mrmlScene.RemoveNode(sn)

#
# MRRectumTDNLMarkerTest
#

class MRRectumTDNLMarkerTest(ScriptedLoadableModuleTest):
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
    self.test_MRRectumTDNLMarker1()

  def test_MRRectumTDNLMarker1(self):
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

    logic = MRRectumTDNLMarkerLogic()

    # Test algorithm with non-inverted threshold
    logic.run(inputVolume, outputVolume)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], 50)

    self.delayDisplay('Test passed')
