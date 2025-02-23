# ai_powered_photo-video_renaming

*This project is mainly programmed by AI.What I did was intergrating and debugging.*

**Please let me know if you encounter any issues!**

> [!IMPORTANT]
>
> Install exiftool before using!

> [!NOTE]
>
> Please note that you need to get an API from ZhipuAI for AI renaming function.

> [!IMPORTANT]
>
> Detailed video metadata extracting has only been tested on Panasonic GH6. Don't highly expect it to be compatible with other cameras.

<img width="1732" alt="Screenshot 2025-02-16 at 19 20 46" src="https://github.com/user-attachments/assets/4d30e821-6cbb-4c78-b0e3-bf6cfa2c98f0" />

## airenamephoto.py

<img width="912" alt="Screenshot 2025-02-16 at 19 19 41" src="https://github.com/user-attachments/assets/d1a459ff-42ef-4819-b045-69d57e373978" />

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

<img width="912" alt="Screenshot 2025-02-16 at 19 19 44" src="https://github.com/user-attachments/assets/52c87f57-2710-41ff-b7b2-4d6922d0db1f" />

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

<img width="712" alt="Screenshot 2025-02-16 at 19 26 06" src="https://github.com/user-attachments/assets/a31431ec-0c5f-4faf-9fa1-0e69e38bb853" />
<img width="1167" alt="Screenshot 2025-02-16 at 19 26 25" src="https://github.com/user-attachments/assets/25642c5c-9dc7-4114-87b0-e267584f5bec" />

