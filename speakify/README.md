# Speakify

A Red bot cog that generates a Speakify-style animated GIF from a user avatar or image attachment.

## Usage

- `[p]speakify` - use your own avatar.
- `[p]speakify @user` - use the mentioned user's avatar.
- `[p]speakify low` - use a lower-quality preset.
- `[p]speakify high @user` - use a high-quality preset with the mentioned user's avatar.
- Attach an image to the command or reply to a message with an image to use that attachment instead of an avatar.

## Notes

- Attachments take priority over avatars.
- The cog uses `Pillow` to generate the animated GIF.
- The `source/assets/speakify.png` asset is used as the target Speakify style image.
