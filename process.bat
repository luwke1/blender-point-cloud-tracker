@echo off
setlocal

:: =================================================================
:: Generic COLMAP Processing Script for Blender Addon
:: This script receives all paths and parameters as arguments.
:: =================================================================

:: Assign arguments to named variables
set "COLMAP_EXE=%~1"
set "DATABASE_PATH=%~2"
set "IMAGES_PATH=%~3"
set "SPARSE_PATH=%~4"
set "MAX_IMAGE_SIZE=%~5"
set "MATCH_OVERLAP=%~6"
set "MAX_FEATURES=%~7"
set "VIDEO_FILENAME=%~8"

echo ================================================================
echo  Starting COLMAP Processing for: %VIDEO_FILENAME%
echo ================================================================
echo.

:: --- COLMAP WORKFLOW ---

echo [1/4] Running Feature Extractor...
"%COLMAP_EXE%" feature_extractor ^
    --database_path "%DATABASE_PATH%" ^
    --image_path "%IMAGES_PATH%" ^
    --ImageReader.single_camera 1 ^
    --SiftExtraction.use_gpu 1 ^
    --SiftExtraction.max_image_size %MAX_IMAGE_SIZE% ^
    --SiftExtraction.max_num_features %MAX_FEATURES%
if errorlevel 1 (
    echo [ERROR] Feature Extractor failed.
    pause & goto :eof
)

echo.
echo [2/4] Running Sequential Matcher...
"%COLMAP_EXE%" sequential_matcher ^
    --database_path "%DATABASE_PATH%" ^
    --SequentialMatching.overlap %MATCH_OVERLAP% ^
    --SiftMatching.use_gpu 1
if errorlevel 1 (
    echo [ERROR] Sequential Matcher failed.
    pause & goto :eof
)

echo.
echo [3/4] Running Mapper (Sparse Reconstruction)...
"%COLMAP_EXE%" mapper ^
    --database_path "%DATABASE_PATH%" ^
    --image_path "%IMAGES_PATH%" ^
    --output_path "%SPARSE_PATH%" ^
    --Mapper.num_threads %NUMBER_OF_PROCESSORS%
if errorlevel 1 (
    echo [ERROR] Mapper failed.
    pause & goto :eof
)

echo.
echo [4/4] Converting model to TXT for import...
if exist "%SPARSE_PATH%\0" (
    "%COLMAP_EXE%" model_converter ^
        --input_path "%SPARSE_PATH%\0" ^
        --output_path "%SPARSE_PATH%" ^
        --output_type TXT
) else (
    echo [WARNING] Sparse model directory not found. Skipping model conversion.
)

echo.
echo ================================================================
echo  COLMAP Processing Finished!
echo ================================================================
echo You can now import the results from the Blender add-on.
endlocal
pause