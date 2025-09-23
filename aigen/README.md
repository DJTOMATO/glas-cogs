# AiGen
A cog for generating images using various AI models.

- Set your API key with [p]set api pollinations token,<your_token>
- Get a Token at https://auth.pollinations.ai/,

# [p]pflux
Image Generation via Pollinations AI (flux model).<br/>
 - Usage: `[p]pflux <prompt>`
# [p]pkontext
Image Generation via Pollinations AI (kontext model).<br/>
 - Usage: `[p]pkontext <prompt>`
# [p]seedream
Image Generation via Pollinations AI (seedream model).<br/>
Can be used with text prompt only or with image attachments.<br/>
 - Usage: `[p]seedream [prompt]`
# [p]pturbo
Image Generation via Pollinations AI (turbo model).<br/>
 - Usage: `[p]pturbo <prompt>`
# [p]referrer
Set the global referrer used in Pollinations API requests.<br/>
 - Usage: `[p]referrer <new_referrer>`
 - Restricted to: `BOT_OWNER`
# [p]hidream
Image Generation using HiDream endpoint.<br/>
 - Usage: `[p]hidream <prompt>`
# [p]flux
Image Generation using Fake-FLUX-Pro-Unlimited endpoint.<br/>
 - Usage: `[p]flux <prompt>`
# [p]lumina
Image Generation using NetaLumina_T2I_Playground endpoint.<br/>
 - Usage: `[p]lumina <prompt>`
# [p]analyze
Analyze an image: provide an attachment, URL, or mention a user (for avatar).<br/>
 - Usage: `[p]analyze [arg]`
# [p]img2img
Multi-Image-to-Image generation via Pollinations AI (kontext model).<br/>
Detects images from attachments, reply, mention, ID, or URL.<br/>
Supports up to 3 images.<br/>
Usage examples:<br/>
!img2img put them together (with 2+ attachments)<br/>
!img2img image1=https://example.com/1.png image2=https://example.com/2.png combine them<br/>
!img2img add a background here @username<br/>
!img2img enhance this 123456789012345678<br/>
!img2img (reply to an image) stylize this<br/>
 - Usage: `[p]img2img [text]`
# [p]elixposearch
Query the Elixposearch model at Pollinations with a text prompt.<br/>
 - Usage: `[p]elixposearch <query>`
# [p]geminisearch
Query the GeminiSearch model at Pollinations with a search prompt.<br/>
 - Usage: `[p]geminisearch <query>`
# [p]gpt5
Query the GPT-5 Nano model at Pollinations with optional image input.<br/>
Usage:<br/>
  [p]gpt5 <prompt> [attach image]<br/>
Examples:<br/>
  [p]gpt5 Tell me a joke<br/>
  [p]gpt5 Describe this in detail (attach an image)<br/>
  [p]gpt5 (just attach an image)<br/>
 - Usage: `[p]gpt5 [query]`
# [p]nanobanana
Image Generation via Pollinations AI (nanobanana model).<br/>
Usage:<br/>
  [p]nanobanana <prompt> [attach image(s), reply, mention, ID, or URL(s)]<br/>
  [p]nanobanana <prompt> (text-only prompt is supported)<br/>
  Multiple images supported (comma-separated).<br/>
 - Usage: `[p]nanobanana [prompt]`
