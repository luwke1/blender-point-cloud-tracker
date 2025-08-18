# Point Cloud Camera Tracker for Blender

A Blender addon that streamlines the process of generating a 3D point cloud and camera track from a single video file using [COLMAP](https://colmap.github.io/).



This tool provides a simple UI panel within Blender to configure and launch the photogrammetry process, automating frame extraction, COLMAP execution, and importing the final result back into your scene.

***

## Features

* **Simple UI:** All controls are located in a clean panel in the 3D Viewport's sidebar.
* **Automated Workflow:** Extracts frames from your video, runs the entire COLMAP pipeline, and prepares the data for import with a single click.
* **Configurable Settings:** Easily adjust key parameters like image resolution, feature count, and frame matching to balance speed and quality.
* **Auto-Import:** Automatically imports the generated point cloud and camera track into Blender once the process is complete.
* **Manual Import:** Options to import the last generated result or any other COLMAP sparse folder.
* **Packaged Dependencies:** Comes with a pre-configured COLMAP executable for Windows, so no separate installation is required.

***

## Requirements

* **Blender:** Version 4.2 or newer.
* **Operating System:** **Windows 64-bit** (due to the included `.bat` script and COLMAP executable).
* **GPU:** A CUDA-enabled NVIDIA GPU is highly recommended for a significant performance boost.
* **Required Addon:** The [Blender-Addon-Photogrammetry-Importer](https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer) must be installed and enabled for the import functionality to work.

***

## Installation

1.  **Install the Importer Addon:**
    * Download the `Blender-Addon-Photogrammetry-Importer` from its [GitHub releases page](https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer/releases).
    * In Blender, go to `Edit > Preferences > Add-ons > Install...` and select the downloaded ZIP file.
    * Find the addon in the list (search for "Photogrammetry") and **enable it** by checking the box.

2.  **Install the Point Cloud Camera Tracker:**
    * Download the ZIP file for this addon.
    * Ensure your unzipped folder structure looks exactly like this (the `bin` folder containing COLMAP must be at the same level as your `__init__.py`):
        ```
        Point-Cloud-Camera-Tracker/
        ├── __init__.py
        ├── process.bat
        └── bin/
            └── win64/
                └── COLMAP/
                    ├── bin/
                    │   └── colmap.exe
                    │   └── ... (other COLMAP files)
                    └── lib/
                        └── ... (other COLMAP files)
        ```
    * In Blender, go to `Edit > Preferences > Add-ons > Install...` and select the addon's ZIP file.
    * Find "Point Cloud Camera Tracker" in the list and **enable it**.

***

## How to Use

1.  **Open the Panel:** In the 3D Viewport, press `N` to open the sidebar. You will find a new tab named **"PCloud Camera Tracker"**.

2.  **Select Video:**
    * Under **1. Video Input**, click the folder icon and select the video file you want to process.

3.  **Adjust Settings:**
    * Under **2. Point Cloud Settings**, you can tweak the following parameters:
        * **Max Image Size:** The maximum resolution for the extracted frames. Smaller values (e.g., 1280) are much faster but less accurate.
        * **Max Features Per Frame:** The maximum number of keypoints to detect in each frame. More features can lead to a denser cloud but increase processing time.
        * **Frame Overlap:** How many subsequent frames to match against each other. Higher values are better for slow-moving footage.

4.  **Generate the Point Cloud:**
    * Under **2. Processing**, ensure **Auto-Import When Done** is checked if you want the results loaded automatically.
    * Click the **Generate Point Cloud** button.
    * A new command prompt/console window will open. **Do not close this window!** It shows the live progress of the COLMAP process. The process is complete when the window says "COLMAP Processing Finished!" and asks you to press any key.

5.  **Import the Results:**
    * **If Auto-Import is enabled**, the point cloud and camera animation will be imported as soon as the console window finishes its work.
    * **For manual import**, use the buttons under **3. Manual Import**:
        * **Import Last Result:** Loads the most recently generated point cloud. This button is only active if a process has been run successfully.
        * **Import from Folder...:** Allows you to navigate to and select any other COLMAP `sparse` folder to import.



***

## How It Works

This addon is a wrapper that orchestrates several tools:

1.  **Frame Extraction:** It uses Blender's built-in Video Sequence Editor (VSE) to render the selected video into a sequence of JPG images. These are saved in a new folder: `[your_video_folder]/colmap_output/[video_name]/images/`.
2.  **COLMAP Processing:** It calls the `process.bat` script, passing all the necessary paths and settings from the UI. This script then executes the main COLMAP commands (`feature_extractor`, `sequential_matcher`, `mapper`) to generate a sparse reconstruction.
3.  **Import:** Once the processing is finished, it uses the `Photogrammetry Importer` addon to read the COLMAP output files (`cameras.txt`, `images.txt`, `points3D.txt`) and create the camera, point cloud, and animation data inside Blender.

***

## Troubleshooting

* **Error: "colmap.exe not found"**: This means the addon cannot find the COLMAP executable. Make sure your installed folder structure matches the one shown in the **Installation** section.
* **Error: "Please enable the 'photogrammetry_importer' add-on."**: You must install and enable the required importer addon first. See step 1 of the installation guide.
* **The process finishes but nothing is imported**: The COLMAP reconstruction might have failed. Check the output in the console window for any errors. Common causes are blurry footage, poor lighting, or scenes with few unique features.
* **Blender freezes when I click "Generate"**: Frame extraction can take a while for long or high-resolution videos. Check the Blender system console (`Window > Toggle System Console`) for progress.