cmake_minimum_required(VERSION 3.13.4)

project(ResearchAdminExtension)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/ResearchAdminExtension")
set(EXTENSION_CATEGORY "Research")
set(EXTENSION_CONTRIBUTORS "Staffan Täckström")
set(EXTENSION_DESCRIPTION "Admin tool for a research study")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/ResearchAdminExtension.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/ResearchAdminExtension/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(StudyAdmin)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
