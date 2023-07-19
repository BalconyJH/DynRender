import asyncio
from os import path
from time import localtime, strftime, time
from typing import Optional

import httpx
import numpy as np
import skia
from dynamicadaptor.Header import Head
from .DynConfig import logger
from .DynStyle import PolyStyle
from .DynTools import get_pictures,paste

class BiliHeader:
    """渲染动态的头部"""

    def __init__(self, static_path: str, style: PolyStyle) -> None:
        self.face_path = path.join(static_path, "Cache", "Face")
        self.pendant_path = path.join(static_path, "Cache", "Pendant")
        self.src_path = path.join(static_path, "Src")
        self.style = style
        self.canvas = None
        self.message = None

    async def run(self, header_message: Head) -> Optional[np.ndarray]:
        try:
            self.message = header_message
            surface = skia.Surface(1080, 400)
            self.canvas = surface.getCanvas()
            self.canvas.clear(skia.Color(*self.style.color.background.normal))
            result = await asyncio.gather(self.paste_logo(),
                                          self.draw_name(),
                                          self.draw_pub_time(),
                                          self.get_face_and_pendant(True),
                                          self.get_face_and_pendant()
                                          )
            await self.past_face(result[3])
            await self.paste_pendant(result[4])
            await self.paste_vip()
            return self.canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        except Exception:
            logger.exception("Error")
            return None

    async def paste_pendant(self, pendant):
        """
        paste pendant onto canvas
        @param pendant:
        @return:
        """
        if pendant is not None:
            pendant = pendant.resize(190, 190)
            await self.paste(pendant, (10, 210))

    async def paste_vip(self):
        if self.message.official_verify and self.message.official_verify.type != -1:
            if self.message.official_verify.type == 0:
                img_path = path.join(self.src_path, "official_yellow.png")
            else:
                img_path = path.join(self.src_path, "official_blue.png")
            img = skia.Image.open(img_path).resize(45, 45)
            await self.paste(img, (120, 330))
        elif self.message.vip and self.message.vip.status == 1:
            if self.message.vip.avatar_subscript == 1:
                img_path = path.join(self.src_path, "big_vip.png")
            else:
                img_path = path.join(self.src_path, "small_vip.png")
            img = skia.Image.open(img_path).resize(45, 45)
            await self.paste(img, (120, 330))

    async def past_face(self, face):
        face = await self.get_face_and_pendant(True)
        if face:
            face = await self.circle_face(face, 120)
            await self.paste(face, (45, 245))

    async def get_face_and_pendant(self, img_type: bool = False):

        if img_type:
            img_name = f"{self.message.mid}.webp"
            img_url = f"{self.message.face}@240w_240h_1c_1s.webp"
            img_path = path.join(self.face_path, img_name)
        elif self.message.pendant and self.message.pendant.image:

            img_name = f"{self.message.pendant.pid}.png"
            img_url = f"{self.message.pendant.image}@360w_360h.webp"
            img_path = path.join(self.pendant_path, img_name)
        else:
            return None
        if path.exists(img_path):
            if time() - int(path.getmtime(img_path)) <= 43200:
                return skia.Image.open(img_path)
        img = await get_pictures(img_url)
        if img is not None:
            img.save(img_path)
            return img
        return None

    async def circle_face(self, img, size):
        surface = skia.Surface(img.dimensions().width(),
                               img.dimensions().height())
        mask = surface.getCanvas()
        paint = skia.Paint(
            Style=skia.Paint.kFill_Style,
            Color=skia.Color(255, 255, 255, 255),
            AntiAlias=True)
        radius = int(img.dimensions().width() / 2)
        mask.drawCircle(radius, radius, radius, paint)

        paint = skia.Paint(
            Style=skia.Paint.kStroke_Style,
            StrokeWidth=5,
            Color=skia.Color(251, 114, 153, 255),
            AntiAlias=True)

        image_array = np.bitwise_and(img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType),
                                     mask.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType))
        canvas = skia.Canvas(image_array, colorType=skia.ColorType.kRGBA_8888_ColorType)
        canvas.drawCircle(radius, radius, radius - 2, paint)
        return skia.Image.fromarray(canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType),
                                    colorType=skia.ColorType.kRGBA_8888_ColorType).resize(size, size)

    async def draw_pub_time(self):
        if self.message.pub_ts:
            pub_time = strftime("%Y-%m-%d %H:%M:%S",
                                localtime(self.message.pub_ts))
        elif self.message.pub_time:
            pub_time = self.message.pub_time
        else:
            pub_time = strftime("%Y-%m-%d %H:%M:%S", localtime(time()))

        await self.draw_text(pub_time,
                             self.style.font.font_family,
                             self.style.font.font_style,
                             skia.Color(
                                 *self.style.color.font_color.sub_title),
                             self.style.font.font_size.time,
                             200, 350)

    async def paste_logo(self) -> None:
        logo = skia.Image.open(path.join(self.src_path, "bilibili.png")).resize(231, 105)
        await self.paste(logo, (433, 20))

    async def draw_name(self):
        # 如果是大会员的话
        if self.message.vip and self.message.vip.status == 1:
            # 如果是大会员名字是粉色
            if self.message.vip.avatar_subscript == 1:
                color = self.style.color.font_color.name_big_vip
            else:
                # 到了愚人节大会员名字会变成绿色
                color = self.style.color.font_color.name_small_vip
        else:
            color = self.style.color.font_color.text
        await self.draw_text(self.message.name,
                             self.style.font.font_family,
                             self.style.font.font_style,
                             skia.Color(*color),
                             self.style.font.font_size.name,
                             200, 300)

    async def draw_text(self, text, font_family, font_style, font_color, font_size, x, y):
        paint = skia.Paint(AntiAlias=True, Color=font_color)
        font_name = None
        offset = x
        font = None
        for i in text:
            if typeface := skia.FontMgr().matchFamilyStyleCharacter(
                    font_family,
                    font_style,
                    ["zh", "en"],
                    ord(i),
            ):
                text_family_name = typeface.getFamilyName()
                if font_name != text_family_name:
                    font_name = text_family_name
                    font = skia.Font(typeface, font_size)

            else:
                font = skia.Font(None, font_size)
            blob = skia.TextBlob(i, font)
            self.canvas.drawTextBlob(blob, offset, y, paint)
            offset += font.measureText(i)

    async def paste(self, image, position: tuple) -> None:
        x, y = position
        img_height = image.dimensions().fHeight
        img_width = image.dimensions().fWidth
        rec = skia.Rect.MakeXYWH(x, y, img_width, img_height)
        self.canvas.drawImageRect(image, skia.Rect(
            0, 0, img_width, img_height), rec)



class RepostHeader:
    def __init__(self,static_path: str, style: PolyStyle) -> None:
        self.style = style
        self.static_path = static_path
    
    async def run(self,message:Head) -> Optional[np.ndarray]:
        surface = skia.Surface(1080,100)
        self.canvas = surface.getCanvas()
        self.canvas.clear(skia.Color(*self.style.color.background.repost))
        try:
            if message.name is None:
                return None
            if message.face is not None:
                pos = 140
                await self.draw_face(message.face,message.mid)
            else:
                pos = 35
            await self.draw_name(message.name,pos)
            return self.canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        except Exception as e:
            logger.exception(e)
            return None
    
    
    async def draw_face(self,url,mid):
        img = await self.get_face(mid,url)
        if img is not None:
            face = await self.circle_face(img,80)
        await paste(self.canvas,face,(40,10))
    
    
    async def draw_name(self,name,pos:int):
        paint = skia.Paint(AntiAlias=True, Color=skia.Color(*self.style.color.font_color.rich_text))
        font_name = None
        offset = pos
        font = None
        for i in name:
            if typeface := skia.FontMgr().matchFamilyStyleCharacter(
                    self.style.font.font_family,
                    self.style.font.font_style,
                    ["zh", "en"],
                    ord(i),
            ):
                text_family_name = typeface.getFamilyName()
                if font_name != text_family_name:
                    font_name = text_family_name
                    font = skia.Font(typeface, self.style.font.font_size.name)

            else:
                font = skia.Font(None,  self.style.font.font_size.name)
            blob = skia.TextBlob(i, font)
            self.canvas.drawTextBlob(blob, offset, 70, paint)
            offset += font.measureText(i)
    
    
    async def circle_face(self, img, size):
        surface = skia.Surface(img.dimensions().width(),
                               img.dimensions().height())
        mask = surface.getCanvas()
        paint = skia.Paint(
            Style=skia.Paint.kFill_Style,
            Color=skia.Color(255, 255, 255, 255),
            AntiAlias=True)
        radius = int(img.dimensions().width() / 2)
        mask.drawCircle(radius, radius, radius, paint)

        paint = skia.Paint(
            Style=skia.Paint.kStroke_Style,
            StrokeWidth=5,
            Color=skia.Color(251, 114, 153, 255),
            AntiAlias=True)

        image_array = np.bitwise_and(img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType),
                                     mask.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType))
        canvas = skia.Canvas(image_array, colorType=skia.ColorType.kRGBA_8888_ColorType)
        canvas.drawCircle(radius, radius, radius - 2, paint)
        return skia.Image.fromarray(canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType),
                                    colorType=skia.ColorType.kRGBA_8888_ColorType).resize(size, size)
    
    async def get_face(self,mid,url):
        img_name = f"{mid}.webp"
        img_url = f"{url}@240w_240h_1c_1s.webp"
        img_path = path.join(self.static_path,"Cache","Face", img_name)
        if path.exists(img_path):
            if time() - int(path.getmtime(img_path)) <= 43200:
                return skia.Image.open(img_path)
        img = await get_pictures(img_url)
        if img is not None:
            img.save(img_path)
        return img