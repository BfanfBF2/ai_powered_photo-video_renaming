# ai_powered_photo-video_renaming

*This project is mainly programmed by AI.What I did was intergrating and debugging.*

**Please let me know if you encounter any issues!**

> [!NOTE]
>
> Please note that you need to get an API from ZhipuAI for AI renaming function.

> [!IMPORTANT]
>
> Detailed video metadata extracting has only been tested on Panasonic GH6. Don't highly expect it to be compatible with other cameras.

## airenamephoto.py

A GUI interface based on tkinter that allows you to read exif data and rename photos with them.Optional data includes:

- Date&Time
- Camera Model
- Lens Model
- Focal Length
- Aperture Value
- Shutter Speed
- ISO Value
- #AI description

## airenamevideo.py

A GUI interface based on tkinter that allows you to read video data and rename video clips with them.AI content recognition is based on extracting frames from videos due to the limitation that too large size video is not supported.Optional data includes:

- Date&Time
- Camera Model
- Resolution
- Frame rate
- Codec
- #AI description

> [!NOTE]
>
> It is currently known that ProRes is not supported.

## 10MBcompressor.py

A GUI interface based on tkinter that automatically detects photos larger than 10MB (To be practical it is actually set to 9MB) and compress them to prevent from the limitation from WeChat Official Accounts editing tools.

