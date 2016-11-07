# Synopsis

Check image and video files for corruption.

# Dependencies

Requires ffmpeg for MP4 and MOV checks.

Linux-based distros: `sudo pip install Pillow OpenEXR pexpect`, also install ffmpeg if required using yum / apt / whatever.

Mac: `pip install Pillow && brew install openexr ffmpeg && sudo pip install openexr pexpect`

# Usage

`python image_verify.py --enable-images --enable-movies --enable-exr /path/to/root/folder/with/images` will check all PNG, JPG, EXR, MOV and MP4 files recursively in specified directory, printing overall stats when finished.

Files with errors are marked with following tags:

- EXR_ERROR: OpenEXR throwed error when calling `OpenEXR.isOpenExrFile`
- PIL_ERROR: File did not pass PIL `Image.verify` test
- FFMPEG_ERROR: File did not pass ffmpeg verification test
- OTHER_ERROR: I/O or system error (access denied, etc)

Use `--verbose` switch to print files being open and files passing the check.

Use `--log-file /path/to/log/file.log` to log all operations to specified log file instead of stdout.
