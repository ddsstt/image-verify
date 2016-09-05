# Synopsis

Check PMG, JPG and EXR files for corruption.

# Dependencies

Linux-based distros: `sudo pip install Pillow OpenEXR`

Mac: `pip install Pillow && brew install openexr && sudo pip install openexr`

# Usage

`python image_verify.py /path/to/root/folder/with/images` will check all PNGs, JPGs and EXRs recursively in specified directory, printing overall stats when finished.

Files with errors are marked with following tags:

- EXR_ERROR: OpenEXR throwed error when calling `OpenEXR.isOpenExrFile`
- PIL_ERROR: File did not pass PIL `Image.verify` test
- OTHER_ERROR: I/O or system error (access denied, etc)

Use `--verbose` switch to print files being open and files passing the check.
