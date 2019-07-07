from aurora.aurlux import Contexter
class Command:
    def __init__(self, func, fname: str = None, **kwargs):
        self.fname = fname
        self.func = func
        self.pres = kwargs.get("pres", [])
        self.posts = kwargs.get("posts", [])
        self.case_sens = kwargs.get("case_sens", True)
        self.onlyme = kwargs.get("onlyme", False)
        self.authtype = kwargs.get("authtype", None)

        if not self.fname:
            self.fname = func.__name__  # type:str
        self.fname = self.fname.lower()


    async def execute(self, ctx: Contexter):

        ctx.called_with = {"name": self.fname, "args": ctx.deprefixed_content[len(self.fname) + 1:], "func":self.func}
        if self.onlyme and ctx.m.author.id != 129706966460137472:
            return
        if not ctx.check_auth():
            return await self.handle_result(ctx, "Insufficient permissions to use this command.")

        pres = [await pre(ctx) for pre in self.pres]
        val = [await self.func(ctx)]
        posts = []
        for post in self.posts:
            args = []
            if post[2] == "ctx":
                args = [ctx]
            if post[1] == "async":
                posts.append(await post[0](*args))
            if post[1] == "sync":
                posts.append(post[0](*args))
        #
        # results = pres + val + posts
        # for result in results:
        #     if not result:
        #         continue
        #     if not isinstance(result, list):
        #         result = [result]
        #     for subresult in result:
        #         await self.handle_result(ctx, subresult)

    # async def handle_result(self, ctx, subresult):
    #     target_channel = "inplace" if "DEFAULT_OUT" not in ctx.config.keys() else ctx.config["DEFAULT_OUT"]
    #     if target_channel == "inplace":
    #         target_channel = ctx.m.channel
    #     else:
    #         target_channel = ctx.find_channel(target_channel, dynamic=True)
    #     if isinstance(subresult, str):
    #         await target_channel.send(subresult)
