shapes = ["portrait", "landscape", "square"]
styles = {
    "Anime": {
        "prompt": "(anime art of [input.description]:1.2), masterpiece, 4k, best quality, anime art",
        "negative": "(worst quality, low quality:1.3), [input.negative], low-quality, deformed, text, poorly drawn, hilariously bad drawing, bad 3D render",
    },
    "Drawn Anime": {
        "prompt": "digital art drawing, illustration of ([input.description]), anime drawing/art, bold linework, illustration, cel shaded, painterly style, digital art, masterpiece",
        "negative": "[input.negative], boring flat infographic, oversaturated, bad photo, terrible 3D render, bad anatomy, worst quality, greyscale, black and white, disfigured, deformed, glitch, cross-eyed, lazy eye, ugly, deformed, distorted, glitched, lifeless, low quality, bad proportions"
    },
    "Cute Anime": {
        "prompt": "(((adorable, cute, kawaii)), [input.description], cute moe anime character portrait, adorable, featured on pixiv, kawaii moé masterpiece, cuteness overload, very detailed, sooooo adorable!!!, absolute masterpiece",
        "negative": "(worst quality, low quality:1.3), [input.negative], worst quality, ugly, 3D, photograph, bad art, blurry, boring"
    },
    "Soft Anime": {
        "prompt": "[input.description], anime masterpiece, soft lighting, intricate, highly detailed, pixiv, anime art, 4k, art from your name anime, garden of words style art, high quality",
        "negative": "(worst quality, low quality:1.3), [input.negative], low-quality, deformed, text, poorly drawn"
    },
    "Waifu": {
        "prompt": "[input.description], waifu character portrait, art by Kazenoko, featured on pixiv, 1 girl, by Ilya Kuvshinov, Kantoku art, very detailed anime art by Redjuice",
        "negative": "(worst quality, low quality:1.3), [input.negative], bad photo, bad art, boring, bad 3D render, worst quality, ugly, blurry, low quality, poorly drawn, bad composition, deformed, bad 3D render, disfigured, bad anatomy, compression artifacts, dead, soulless, photorealistic",
    },
    "Vintage Anime": {
        "prompt": "[input.description], 1990s anime, vintage anime, 90's anime style, by hajime sorayama, by greg tocchini, anime masterpiece, pixiv, akira-style art, akira anime art, 4k, high quality",
        "negative": "[input.negative], (worst quality, low quality:1.3), bad art, distorted, deformed",
    },
    "Neon Vintage Anime": {
        "prompt": "[input.description], ((neon vintage anime)) style, 90's anime style, 1990s anime, hajime sorayama, greg tocchini, neon vintage anime masterpiece, anime art, 4k, high quality",
        "negative": "[input.negative], blurry, (worst quality, low quality:1.3), bad art, distorted, deformed",
    },
    "Manga": {
        "prompt": "[input.description], incredible hand-drawn manga, black and white, by Takehiko Inoue, by Katsuhiro Otomo and akira toriyama manga, hand-drawn art by rumiko takahashi and Inio Asano, Ken Akamatsu manga art",
        "negative": "[input.negative], (worst quality, low quality:1.3), bad photo, bad 3D render, distorted, deformed, fuzzy, noisy, blurry, smudge",
    },

    "Digital Painting": {
        "prompt": "[input.description], breathtaking digital art, trending on artstation, by atey ghailan, by greg rutkowski, by greg tocchini, by james gilleard, 8k, high resolution, best quality",
        "negative": "[input.negative], low-quality, deformed, signature watermark text, poorly drawn"
    },

    "Oil Painting": {
        "prompt": "breathtaking alla prima oil painting, [input.description], close up, (alla prima style:1.3), oil on linen, painterly oil on canvas, (painterly style:1.3), exquisite composition and lighting, modern painterly masterpiece, by alexi zaitsev, award-winning painterly alla prima oil painting",
        "negative": "[input.negative], framed, faded colors, terrible photo, bad composition, hilariously bad drawing, bad photo, bad anatomy, extremely high contrast, worst quality, watermarked signature, bad colors, deformed, amputee, washed out, glare, boring colors, bad crayon drawing"
    },
    "Oil Painting - Realism": {
        "prompt": "breathtaking oil painting, [input.description], photorealistic oil painting, by charlie bowater, fine details, by wlop, trending on artstation, very detailed",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn, worst quality"
    },
    "Fantasy Painting": {
        "prompt": "[input.description], d&d, fantasy, highly detailed, digital painting, artstation, sharp focus, fantasy art, illustration, 8k, in the style of greg rutkowski",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn"
    },
    "Fantasy Landscape": {
        "prompt": "[input.description], fantasy matte painting, absolute masterpiece, detailed matte painting by andreas rocha and greg rutkowski, by Brothers Hildebrandt, superb composition, vivid fantasy art, breathtaking fantasy masterpiece",
        "negative": "[input.negative], faded, blurry, bad art, boring"
    },
    "Fantasy Portrait": {
        "prompt": "[input.description], d&d, fantasy, highly detailed, digital painting, artstation, sharp focus, fantasy art, character art, illustration, 8k, art by artgerm and greg rutkowski",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn"
    },
    "Studio Ghibli": {
        "prompt": "[input.description], (studio ghibli style art:1.3), sharp, very detailed, high resolution, inspired by hayao miyazaki, anime, art from ghibli movie",
        "negative": "(worst quality, low quality:1.3), [input.negative], low-quality, deformed, text, poorly drawn"
    },
    "Medieval": {
        "prompt": "medieval illuminated manuscript picture of [input.description], medieval illuminated manuscript art, masterpiece medieval color illustration, 16th century, 8k high-resolution scan of 16th century illuminated manuscript painting, detailed medieval masterpiece, close-up",
        "negative": "[input.negative], worst quality, blurry"
    },
    "Pixel Art": {
        "prompt": "[input.description.length > 40 ? '(pixel art), ' : ''][input.description], best pixel art, neo-geo graphical style, retro nostalgic masterpiece, 128px, 16-bit pixel art [input.description.length < 10 ? 'of ' + input.description : ''], 2D pixel art style, adventure game pixel art, inspired by the art style of hyper light drifter, masterful dithering, superb composition, beautiful palette, exquisite pixel detail",
        "negative": "[input.negative], glitched, deep fried, jpeg artifacts, out of focus, gradient, soft focus, low quality, poorly drawn, blur, grainy fabric texture, text, bad art, boring colors, blurry platformer screenshot"
    },
    "Furry - Painted": {
        "prompt": "anthro [input.description] digital art, masterpiece, 4k, fine details",
        "negative": "[input.negative], bad photo, worst quality, bad composition, bad lighting, bad colors, small eyes, low quality, bad art, poorly drawn, deformed, bad 3D render, boring, lifeless, deformed, ugly, low resolution"
    },
    "Furry - Drawn": {
        "prompt": "anthro [input.description] illustration, hand-drawn, bold linework, anthro illustration, cel shaded, 4k, fine details, masterpiece",
        "negative": "[input.negative], bad photo, terrible 3D render, bad anatomy, worst quality, greyscale, black and white, disfigured, deformed, glitch, cross-eyed, lazy eye, ugly, deformed, distorted, glitched, lifeless, low quality, bad proportions"
    },
    "Illustration": {
        "prompt": "breathtaking illustration of [input.description], (illustration:1.3), masterpiece, breathtaking illustration",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn, bad 3D render, bad composition, bad photo, worst quality"
    },
    "Watercolor": {
        "prompt": "[input.description], (watercolor), high resolution, intricate details, 4k, wallpaper, concept art, watercolor on textured paper",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn"
    },
    "1990s Photo": {
        "prompt": "[input.description], 90s home video, nostalgic 90s photo, taken with kodak disposable camera",
        "negative": "[input.negative], blurry, blur, deformed"
    },
    "1980s Photo": {
        "prompt": "famous vintage 80s photo, [input.description], grainy photograph, 80s photo with film grain, Kodacolor II 80s photo with vignetting, retro, r/OldSchoolCool, 80s photo with wear and tear and minor creasing and scratches, vintage color photo",
        "negative": "[input.negative], deformed"
    },
    "1970s Photo": {
        "prompt": "famous vintage 70s photo, [input.description], grainy photograph, 1970s photo with film grain, 70s photo with vignetting, retro, r/OldSchoolCool, 70s photo, vintage photo",
        "negative": "[input.negative], deformed"
    },
    "50s Infomercial Anime": {
        "prompt": "[input.description], 1950s infomercial style, (delicate linework:1.1), paprika anime art style, close-up, (chromatic aberration glow:1.2), 2d painted cel animation, close-up, soft focus, 2D pixiv 1950s",
        "negative": "worst quality, low quality, [input.negative], neon tube, bad art, messy, disfigured, bad anatomy, out of focus, grainy, blurry, jpeg artifact noise, deformed"
    },    
    "3D Pokemon": {
        "prompt": "a pokemon creature, (([input.description])), 4k render, beautiful pokemon digital art, fakemon, pokemon creature, cryptid, fakemon, masterpiece, {soft|sharp} focus, (best quality, high quality:1.3)",
        "negative": "[input.negative], distorted, deformed, bad art, low quality, over saturated, extreme contrast, (worst quality, low quality:1.3)"
    },
    "Painted Pokemon": {
        "prompt": "([input.description]), 4k digital painting of a pokemon, amazing pokemon creature art by piperdraws, cryptid creations by Piper Thibodeau, by Naoki Saito and {Tokiya|Mitsuhiro Arita}, incredible composition",
        "negative": "[input.negative], crappy 3D render, distorted, deformed, bad art, low quality, text, signature"
    },
    "2D Pokemon": {
        "prompt": "([input.description]:1.2), pokemon creature concept, superb line art, beautiful colors and composition, 2d art style, beautiful pokemon digital art, fakemon, by Sowsow, pokemon creature, cryptid, fakemon, masterpiece, by Yuu Nishida, 4k",
        "negative": "[input.negative], multiple, grid, (black and white), distorted, deformed, bad art, low quality, crappy 3D render, text watermark symbols logo"
    },

    "Crayon Drawing": {
        "prompt": "[input.description], crayon drawing",
        "negative": "[input.negative], low-quality, deformed, text, poorly drawn"
    },
    "Pencil": {
        "prompt": "((black and white pencil drawing)), [input.description], black and white, breathtaking pencil illustration, highly detailed, 4k, (textured paper), pencil texture, sketch",
        "negative": "[input.negative], stationary, holding pen, holding paper, low-quality, deformed, photo, 3D render, text, poorly drawn"
    },
    "Tattoo Design": {
        "prompt": "amazing tattoo design, [input.description], breathtaking tattoo design, incredible tattoo design",
        "negative": "[input.negative], low-quality, poorly drawn, blurry, faded, terrible design, worst quality, deformed, amputee, disfigured, ugly, bad, shitty, boring"
    },
    "Traditional Japanese": {
        "prompt": "[input.description], in ukiyo-e art style, traditional japanese masterpiece",
        "negative": "[input.negative], blurry, low resolution, worst quality, fuzzy"
    },
    "Nihonga Painting": {
        "prompt": "japanese nihonga painting about [input.description], Nihonga, ancient japanese painting, intricate, detailed",
        "negative": "[input.negative], framed blurry crappy photo, overly faded"
    },
    "Cartoon": {
        "prompt": "[input.description], cartoon-style art, superb linework, nice colors and composition, bold linework, close-up, (masterpiece), cute art by Dana Terrace, by Rebecca Sugar, by ry-spirit, amazing and wholesome cartoon-style art, cute art style, (trending on artstation)",
        "negative": "[input.negative], bad art, boring art, hilariously bad drawings, bad 3D render, bad photo, blurry, blur, worst quality, boring colors, logo vector image, monotone, lifeless, expressionless, faded, horror, creepy"
    },
    "Cursed Photo": {
        "prompt": "cursed photo of [input.description], (creepy and cursed:1.2), absolutely cursed photo, nope nope nope nope, what the actual f, (unsettling photo:1.2), cursed_thing, cursedimages, no context, cursed image, bad photo, weird photo, very strange, color photo, creepy photo, (nightmare fuel)",
        "negative": "[input.negative], skeleton face, nice photo, lovely photo, old photo, vintage photo, greyscale, wholesome, eyebleach, bad photoshop"
    }
}
