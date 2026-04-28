# AiGen

Set your API key with [p]set api pollinations token,<your_token>
Get a Token at https://enter.pollinations.ai/",

# AiGen

A cog for generating images using various AI models.<br/>Type ``!help text`` to see text commands

## [p]text

Text AI commands.<br/>

 - Usage: `[p]text`

### [p]text gemini

Query with `gemini`.<br/>

 - Usage: `[p]text gemini [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text mistral

Query with `mistral`.<br/>

 - Usage: `[p]text mistral [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text midijourney

Query with `midijourney`.<br/>

 - Usage: `[p]text midijourney [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text qwencharacter

Query with Qwen Character model.<br/>

Model: qwen-character<br/>

 - Usage: `[p]text qwencharacter [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text mistralfast

Query with `mistral-fast`.<br/>

 - Usage: `[p]text mistralfast [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text chickytutor

Query with `chickytutor`.<br/>

 - Usage: `[p]text chickytutor [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text deepseek

Query with `deepseek`.<br/>

 - Usage: `[p]text deepseek [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text openai

Query with `openai`.<br/>

 - Usage: `[p]text openai [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text novamicro

Query with Amazon Nova Micro model.<br/>

Model: nova-fast<br/>

 - Usage: `[p]text novamicro [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text perplexityfast

Query with `perplexity-fast`.<br/>

 - Usage: `[p]text perplexityfast [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text gemini3

Query via Gemini3<br/>

 - Usage: `[p]text gemini3 [query]`
 - Cooldown: `1 per 60.0 seconds`

### [p]text openaifast

Query with `openai-fast`.<br/>

 - Usage: `[p]text openaifast [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text grok

Query with `grok`.<br/>

 - Usage: `[p]text grok [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text geminisearch

Query via gemini-search<br/>

 - Usage: `[p]text geminisearch [query]`
 - Cooldown: `1 per 60.0 seconds`

### [p]text minimax

Query with MiniMax M2.1 model.<br/>

Model: minimax<br/>

 - Usage: `[p]text minimax [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text perplexityreasoning

Query with `perplexity-reasoning`.<br/>

 - Usage: `[p]text perplexityreasoning [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text claude

Query with `claude`.<br/>

 - Usage: `[p]text claude [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text openailarge

Query with `openai-large`.<br/>

 - Usage: `[p]text openailarge [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text kimik2thinking

Query with `kimi-k2-thinking`.<br/>

 - Usage: `[p]text kimik2thinking [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text kimi

Query with Moonshot Kimi K2.5 model.<br/>

Model: kimi<br/>

 - Usage: `[p]text kimi [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text openaireasoning

Query with `openai-reasoning`.<br/>

 - Usage: `[p]text openaireasoning [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text qwencoder

Query with `qwen-coder`.<br/>

 - Usage: `[p]text qwencoder [query]`
 - Cooldown: `3 per 5.0 seconds`

### [p]text glm

Query with Z.ai GLM-4.7 model.<br/>

Model: glm<br/>

 - Usage: `[p]text glm [query]`
 - Cooldown: `3 per 5.0 seconds`

## [p]settings

Settings commands.<br/>

 - Usage: `[p]settings`

### [p]settings externalupload

Enable or disable external uploads like Chibisafe for this server.<br/>

 - Usage: `[p]settings externalupload <toggle>`
 - Restricted to: `ADMIN`

### [p]settings referrer

Set the global referrer used in Pollinations API requests.<br/>

 - Usage: `[p]settings referrer <new_referrer>`
 - Restricted to: `BOT_OWNER`

## [p]flux

Generate an image using the Flux model.<br/>

Model: flux<br/>

 - Usage: `[p]flux <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]turbo

Generate an Image via turbo model.<br/>

Model: turbo<br/>

 - Usage: `[p]turbo <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]zimage

Generate an Image via Z-Image Turbo model.<br/>

Model: zimage<br/>

 - Usage: `[p]zimage <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]imagen

Generate an Image via Imagen 4 model.<br/>

Model: imagen-4<br/>

 - Usage: `[p]imagen <prompt>`
 - Cooldown: `1 per 60.0 seconds`

## [p]hidream

Generate an Image via HiDream endpoint.<br/>

 - Usage: `[p]hidream <prompt>`
 - Cooldown: `1 per 10.0 seconds`

## [p]analyze

Analyze an image: provide an attachment, URL, or mention a user (for avatar).<br/>

 - Usage: `[p]analyze [arg]`
 - Cooldown: `1 per 60.0 seconds`

## [p]img2img

Multi-Image-to-Generate an Image via gptimage model.<br/>

Model: flux<br/>

Detects images from attachments, reply, mention, ID, or URL.<br/>
Supports up to 3 images.<br/>

Usage examples:<br/>
- !img2img put them together (with 2+ attachments)<br/>
- !img2img add a background here @username<br/>
- !img2img enhance this 123456789012345678<br/>
- !img2img (reply to an image) stylize this<br/>

 - Usage: `[p]img2img [text]`
 - Cooldown: `1 per 60.0 seconds`

## [p]gptimage

Generate an Image via gptimage model.<br/>

Model: gptimage<br/>
Max size is 1024x1024<br/>
Usage:<br/>
  [p]gptimage <prompt> [attach image(s), reply, mention, ID, or URL(s)]<br/>
  [p]gptimage <prompt> (text-only prompt is supported)<br/>
  Multiple images supported (comma-separated).<br/>

 - Usage: `[p]gptimage [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]seedance

Generate videos using Seedance Lite model.<br/>

Model: seedance<br/>

 - Usage: `[p]seedance [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]wan

Generate videos using Wan model.<br/>

Model: Wan<br/>

 - Usage: `[p]wan [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]grokvideo

Generate videos using Grok Video model.<br/>

Model: grok-video<br/>

Supports text-to-video generation.<br/>

Usage:<br/>
!grok-video a girl dancing in a field<br/>
!grok-video --duration 5 a person waving<br/>

 - Usage: `[p]grokvideo [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]klein

Generate an Image via FLUX.2 Klein 4B model.<br/>

Model: klein<br/>
Max size is 2048x2048<br/>
Usage:<br/>
  [p]klein <prompt> [attach image(s), reply, mention, ID, or URL(s)]<br/>
  [p]klein <prompt> (text-only prompt is supported)<br/>
  Multiple images supported (comma-separated).<br/>

 - Usage: `[p]klein [prompt]`
 - Cooldown: `1 per 60.0 seconds`

## [p]kleinpro

Generate an Image via FLUX.2 Klein 9B model.<br/>

Model: klein-large<br/>
Max size is 2048x2048<br/>
Usage:<br/>
  [p]kleinpro <prompt> [attach image(s), reply, mention, ID, or URL(s)]<br/>
  [p]kleinpro <prompt> (text-only prompt is supported)<br/>
  Multiple images supported (comma-separated).<br/>

 - Usage: `[p]kleinpro [prompt]`
 - Cooldown: `1 per 60.0 seconds`

