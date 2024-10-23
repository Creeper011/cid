from discord.ext import commands
import os

class DynamicCogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def find_extension(self, extension_name):
        base_dir = "extensions"
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file == f"{extension_name}.py":
                    path = os.path.join(root, file)
                    extension_path = os.path.splitext(os.path.relpath(path, base_dir))[0].replace(os.path.sep, ".")
                    return f"{base_dir}.{extension_path}"
        return None

    @commands.command(name="unload")
    @commands.is_owner()
    async def unload_command(self, ctx, extension_name: str):
        try:
            extension = await self.find_extension(extension_name)
            if extension in self.bot.extensions:
                await self.bot.unload_extension(extension)
                await ctx.send(f"Extensão {extension_name} descarregada.")
            else:
                await ctx.send(f"Extensão {extension_name} não está carregada ou não foi encontrada.")
        except Exception as e:
            await ctx.send(f"Erro ao descarregar extensão {extension_name}: {e}")

    @commands.command(name="load")
    @commands.is_owner()
    async def load_command(self, ctx, extension_name: str):
        try:
            extension = await self.find_extension(extension_name)
            if extension and extension not in self.bot.extensions:
                await self.bot.load_extension(extension)
                await ctx.send(f"Extensão {extension_name} carregada.")
        except Exception as e:
            await ctx.send(f"Erro ao carregar extensão {extension_name}: {e}")

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_command(self, ctx, extension_name: str):
        try:
            extension = await self.find_extension(extension_name)
            if extension and extension in self.bot.extensions:
                await self.bot.reload_extension(extension)
                await ctx.send(f"Extensão {extension_name} recarregada.")
            else:
                await ctx.send(f"Extensão {extension_name} não está carregada ou não foi encontrada.")
        except Exception as e:
            await ctx.send(f"Erro ao recarregar extensão {extension_name}: {e}")

async def setup(bot):
    await bot.add_cog(DynamicCogs(bot))
