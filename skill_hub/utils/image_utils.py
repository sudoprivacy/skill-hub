import os
import io
from google import genai
from google.genai import types
from PIL import Image

class AppIconGenerator:
    def __init__(self, api_key=None, output_dir="./icons"):
        """
        初始化工具类。
        :param api_key: Gemini API Key。如果不传，默认使用系统内置的 API Key。
        :param output_dir: 生成的 64x64 图标保存的本地目录
        """
        # 默认使用环境内置的 API Key
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "AIzaSyDDu3RaI_rpYghg7IbqRsdsUErAv0c1k88")
        self.client = genai.Client(api_key=self.api_key)
        self.output_dir = output_dir
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _generate_image_prompt(self, app_description: str) -> str:
        """
        第一步：调用 Gemini 文字模型，将 APP 的描述转化为精美的 Image Prompt
        """
        print("🤖 [Step 1] 正在根据 App 描述生成优化后的图像提示词...")
        
        system_instruction = (
            "You are a professional App Icon Designer and Midjourney/DALL-E prompt engineer. "
            "Your task is to take an app's description and generate a single, highly detailed, "
            "vibrant, and minimalist image generation prompt for an iOS/Android app icon. "
            "The icon should be visually striking, centered, transparent background, 3D/flat hybrid style. "
            "DO NOT output any conversational text, ONLY output the raw image prompt string."
        )
        
        user_message = f"App Description: {app_description}\n\nPlease generate the image prompt for its icon."
        
        # 使用 gemini-2.5-flash 进行提示词专业扩写
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        
        generated_prompt = response.text.strip()
        print(f"📝 优化后的提示词: {generated_prompt}\n")
        return generated_prompt

    def _generate_and_resize_icon(self, image_prompt: str, filename: str):
        """
        第二步：调用 Gemini Image 模型生成原图，并裁剪为 64x64 PNG
        """
        print("🎨 [Step 2] 正在调用 Gemini Image 模型生成图片...")
        
        try:
            # 调用 gemini-3.1-flash-image-preview 生成图片
            result = self.client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=image_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio="1:1",
                        image_size="512"
                    )
                )
            )
            
            # 解析返回的图片二进制数据
            if result.candidates and result.candidates[0].content.parts:
                part = result.candidates[0].content.parts[0]
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_bytes = part.inline_data.data
                    
                    # 使用 Pillow 处理图像：读取、缩放、转换为 64x64 PNG
                    print("📏 [Step 3] 正在将图片重采样为 64x64 分辨率的 PNG...")
                    image = Image.open(io.BytesIO(image_bytes))
                    img_rgba = image.convert('RGBA')
                    # 调整大小，使用 Lanczos 高质量重采样
                    resized_image = img_rgba.resize((128, 128), Image.Resampling.LANCZOS)
                    
                    output_path = os.path.join(self.output_dir, filename)
                    # 确保保存为 PNG 格式
                    resized_image.save(output_path, format="PNG")
                    print(f"✅ 成功！Icon 已保存至: {os.path.abspath(output_path)}")
                    return output_path
                else:
                    print("❌ 生成失败：未返回图像数据。")
            else:
                print("❌ 生成失败：API 响应为空。")
        except Exception as e:
            print(f"❌ 图像生成发生错误: {e}")

    def create_icon(self, app_description: str, output_filename: str = "app_icon.png"):
        """
        对外暴露的主方法：传入 app 描述，自动完成全流程并保存文件
        """
        image_prompt = self._generate_image_prompt(app_description)
        return self._generate_and_resize_icon(image_prompt, output_filename)


# 直接运行测试
if __name__ == "__main__":
    generator = AppIconGenerator(output_dir="./icons")
    
    app_desc = "用现代Rust构建高性能且内存安全的应用"
    
    generator.create_icon(
        app_description=app_desc, 
        output_filename="pomodoro_timer_icon.png"
    )
