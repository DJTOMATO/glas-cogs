# AiGen

A cog for generating images, text and audio using various AI models via Pollinations.ai.

## [p]aigen

AI generation commands and settings.<br/>

 - Usage: `[p]aigen`

### [p]aigen text

Text AI commands.<br/>

 - Usage: `[p]aigen text`

### [p]aigen aisettings

Settings commands.<br/>

 - Usage: `[p]aigen aisettings`

#### [p]aigen aisettings referrer

Set the global referrer used in Pollinations API requests.<br/>

 - Usage: `[p]aigen aisettings referrer <new_referrer>`
 - Restricted to: `BOT_OWNER`

#### [p]aigen aisettings externalupload

Enable or disable external uploads like Chibisafe for this server.<br/>

 - Usage: `[p]aigen aisettings externalupload <toggle>`
 - Restricted to: `ADMIN`

## [p]pollen (Hybrid Command)

Show current Pollen balance, recent usage, and refill timer.<br/>

 - Usage: `[p]pollen`
 - Slash Usage: `/pollen`

## [p]image (Hybrid Command)

Generate an image using various AI models.<br/>

 - Usage: `[p]image <model> <prompt> [negative_prompt=None] [width=None] [height=None] [seed=None] [image=None]`
 - Slash Usage: `/image <model> <prompt> [negative_prompt=None] [width=None] [height=None] [seed=None] [image=None]`

## [p]text (Hybrid Command)

Query AI text models.<br/>

 - Usage: `[p]text <model> <query> [image=None] [temperature=1.0] [max_tokens=4096]`
 - Slash Usage: `/text <model> <query> [image=None] [temperature=1.0] [max_tokens=4096]`

## [p]video (Hybrid Command)

Generate a short video from text or image.<br/>

 - Usage: `[p]video <model> <prompt> [duration=5] [image=None]`
 - Slash Usage: `/video <model> <prompt> [duration=5] [image=None]`

## [p]audio (Hybrid Command)

Generate audio or music from text.<br/>

 - Usage: `[p]audio <model> <prompt> [duration=30]`
 - Slash Usage: `/audio <model> <prompt> [duration=30]`

## [p]flux

Generate an image using Flux.<br/>

 - Usage: `[p]flux <prompt>`
 - Cooldown: `1 per 3.0 seconds`

## [p]flux2

Generate an image using Flux-2-Dev with image-to-image support.<br/>

 - Usage: `[p]flux2 [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]turbo

Generate an image via turbo model.<br/>

 - Usage: `[p]turbo <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]zimage

Generate an image via Z-Image model.<br/>

 - Usage: `[p]zimage <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]imagen

Generate an image via Imagen-4 model.<br/>

 - Usage: `[p]imagen <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]gimagine

Generate an image via Grok-Imagine model.<br/>

 - Usage: `[p]gimagine <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]img2img

Generate an image using Flux based on other images.<br/>

 - Usage: `[p]img2img [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]klein

Generate an image via Klein model.<br/>

 - Usage: `[p]klein [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]kleinpro

Generate an image via Klein-Large model.<br/>

 - Usage: `[p]kleinpro [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]wanimage

Generate an Image via wan-image model.<br/>

 - Usage: `[p]wanimage [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]qwenimage

Generate an Image via qwen-image model.<br/>

 - Usage: `[p]qwenimage [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]gptimage

Generate an Image via gpt-image-2 model.<br/>

 - Usage: `[p]gptimage [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]hidream

Generate an Image via HiDream endpoint.<br/>

 - Usage: `[p]hidream <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]linkedin

Transform text into LinkedIn-style post (v1).<br/>

 - Usage: `[p]linkedin [query]`
 - Cooldown: `1 per 60.0 seconds`

## [p]linkedin2

Transform text into LinkedIn-style post (v2).<br/>

 - Usage: `[p]linkedin2 [query]`
 - Cooldown: `1 per 60.0 seconds`

## [p]analyze

Analyze an image using AI.<br/>

 - Usage: `[p]analyze [arg]`
 - Cooldown: `1 per 60.0 seconds`

## [p]nova_reel

Generate video via Nova-Reel.<br/>

 - Usage: `[p]nova_reel [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]ltx_video

Generate video via LTX-2.<br/>

 - Usage: `[p]ltx_video [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]qwentts_audio

Generate audio via qwen3 model.<br/>

 - Usage: `[p]qwentts_audio <prompt>`
 - Cooldown: `3 per 5.0 seconds`

