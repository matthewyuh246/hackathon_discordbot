import os
import discord
from discord.ext import commands
from random import choice
from dotenv import load_dotenv 

load_dotenv() 

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

alreadySetArea = False

gomiWeekList = []

esaCallList = []

dayCnt = [0] * 6  # 何日経ったか、要素数が何日か表す
workEsaList = [0] * 6
workEatList = [0] * 6


checkList = [0, 0]  # true, false

gomiEnergy = []


areaDict = {
    "生田": [0, 5, 2, 0, 4, 1],
    "和泉": [2, 4, 0, 1, 5, 0],
    "栗谷": [0, 5, 2, 0, 4, 1],
    "宿河原": [2, 4, 0, 1, 5, 0],
    "菅": [0, 5, 2, 0, 4, 1],
    "菅稲田堤": [0, 5, 2, 0, 4, 1],
    "菅北浦": [0, 5, 2, 0, 4, 1],
    "菅城下": [0, 5, 2, 0, 4, 1],
    "菅仙谷": [0, 5, 2, 0, 4, 1],
    "菅野戸呂": [0, 5, 2, 0, 4, 1],
    "菅馬場": [0, 5, 2, 0, 4, 1],
    "堰": [2, 4, 0, 1, 5, 0],
    "寺尾台": [0, 5, 2, 0, 4, 1],
    "長尾": [4, 1, 0, 5, 3, 0],
    "長沢": [0, 2, 5, 0, 1, 4],
    "中野島": [4, 1, 0, 5, 3, 0],
    "西生田": [0, 2, 5, 0, 1, 4],
    "登戸": [2, 4, 0, 1, 5, 0],
    "登戸新町": [2, 4, 0, 1, 5, 0],
    "東生田": [4, 1, 0, 5, 3, 0],
    "東三田": [4, 1, 0, 5, 3, 0],
    "布田": [4, 1, 0, 5, 3, 0],
    "枡形": [4, 1, 0, 5, 3, 0],
    "三田": [4, 1, 0, 5, 3, 0],
    "南生田": [0, 2, 5, 0, 1, 4],
}

gomiMatchDayDict = {
    0: "燃えるゴミ",
    1: "プラスチック",
    2: "缶・ビン・ペットボトル",
    3: "ペットボトル",
    4: "ミックスペーパー(雑紙)",
    5: "収集なし",
}

days = ["月曜日 : ", "火曜日 : ", "水曜日 : ", "木曜日 : ", "金曜日 : ", "土曜日 : "]

esaDict = {
    # 燃えるゴミ : 0
    "魚の骨": 0,
    "アイスキャンディの棒": 0,
    "セミ": 0,
    "業務スーパーの焼き鳥を食べた後のくし(タレ付き)": 0,
    "鼻を噛んだティッシュ": 0,
    "オカリナ": 0,
    "起き上がり小法師": 0,
    "パーティのあとの紙コップ": 0,
    "ピザの箱": 0,
    # プラ : 1
    "ポテトチップスの袋": 1,
    "車のワックスのボトル": 1,
    "コンタクトレンズの容器": 1,
    "ペットボトルのラベル": 1,
    "レジ袋": 1,
    "切るの失敗したラップ": 1,
    "梱包のプチプチ": 1,
    # 缶・びん : 2
    "お菓子の缶": 2,
    "マイケルが飲んだピンモンの空き缶": 2,
    "非常食の缶": 2,
    "アルミ缶": 2,
    "スプレー缶": 2,
    "ラムネのびん": 2,
    "ごま油のびん": 2,
    "ワインのびん": 2,
    "田中さん缶": 2,
    # ペットボトル : 3
    "ファソタのペットボトル": 3,
    "1週間放置された麦茶のペットボトル": 3,
    "綺麗なお水で洗われたペットボトル": 3,
    "Java Teaのペットボトル": 3,
    "ウォーターサーバーのペットボトル": 3,
    "Wow!!お茶": 3,
    # ミックスペーパー : 4
    "新聞に挟まっている広告": 4,
    "アイスクリームのふた": 4,
    "アルミホイルの芯": 4,
    "牛乳パック": 4,
    "チョコレートの包み紙": 4,
    "お道具箱(紙製)": 4,
    "綺麗な紙コップ": 4,
    "チップスターの容器": 4,
}


# discord.ui.Button を継承
class DeleteButton(discord.ui.Button):
    # コンストラクタの引数に user を追加
    def __init__(
        self,
        user: discord.User,
        style=discord.ButtonStyle.red,
        label="Delete",
        **kwargs
    ):
        self.user_id = user.id  # クラス変数にユーザ ID を保存
        super().__init__(style=style, label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        # 保存したユーザとボタンを押したユーザが同じかどうか
        if self.user_id == interaction.user.id:
            massageContent = interaction.message.content
            print("削除: ", massageContent)
            esaCallList.remove(massageContent)
            print(esaCallList)
            await interaction.message.delete()


# discord.ui.Button を継承
class SelectButton(discord.ui.Button):
    # コンストラクタの引数に user を追加
    def __init__(
        self,
        user: discord.User,
        style=discord.ButtonStyle.gray,
        label="Select",
        **kwargs
    ):
        self.user_id = user.id  # クラス変数にユーザ ID を保存
        super().__init__(style=style, label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        # 保存したユーザとボタンを押したユーザが同じかどうか
        if self.user_id == interaction.user.id:
            if len(areaDict) > 1:
                self.selectArea = interaction.message.content
                print("あんたの地域は" + self.selectArea)
                areaDictKeys = list(areaDict.keys())
                for i in areaDictKeys:  # 選んだもの以外を全部削除する。
                    if i == self.selectArea:
                        pass
                    else:
                        del areaDict[i]
                # 地域のリスト設定
                gomiWeekList_temp = list(areaDict.values())
                print(gomiWeekList_temp[0][0])
                for i in range(6):
                    gomiWeekList.append(gomiWeekList_temp[0][i])

                print(gomiWeekList)
            else:
                print("地域はもう" + str(areaDict.keys()) + "に設定されているよ")
            await interaction.message.delete()


@bot.command()
async def esa(ctx: commands.Context):
    print("お前", len(workEsaList))
    print("へ", len(dayCnt) + 1)
    if gomiWeekList[6 - len(dayCnt)] == 5:
        await ctx.send("今日はゴミ回収、無い日だよ〜")
    elif len(workEsaList) == len(dayCnt):
        await ctx.send("今日見つけるべきもの : " + gomiMatchDayDict[gomiWeekList[6 - len(dayCnt)]])
        print("お前は" + str(areaDict.keys()))
        print("エナジー" + str(gomiEnergy))
        print("でいcnt" + str(len(dayCnt)))
        if len(dayCnt) > 0 and len(areaDict) == 1:
            view = discord.ui.View()
            delete_button = DeleteButton(ctx.author)  # コマンドを呼んだユーザを渡す
            view.add_item(delete_button)  # 作ったボタンを view に追加
            for i in range(15):
                esaCall = choice(list(esaDict.keys()))
                esaCallList.append(esaCall)
                print(esaCallList)
                await ctx.send(esaCall, view=view)  # view と一緒にメッセージを送信
            workEsaList.remove(0)
        else:
            await ctx.send("もうお腹いっぱいだよォ")
    else:
        await ctx.send("これ以上のゴミは無いよォ")


@bot.command()
async def eat(ctx: commands.Context):
    print("お前の地域は" + str(areaDict.keys()))
    if len(workEatList) == len(dayCnt):
        if esaCallList != [] and len(areaDict) == 1 and len(dayCnt) > 0:
            # エサの正誤判定
            rightEsa = []
            rightEsa.append(gomiWeekList[6 - len(dayCnt)])
            if rightEsa[0] == 2:
                rightEsa.append(3)
            print("okなえさ", rightEsa)
            for i in range(len(esaCallList)):
                # gomiWeekList[6 - len(dayCnt)] でその日が何ゴミ回収日かわかる
                if esaDict[esaCallList[0]] in rightEsa:
                    checkList[0] += 1  # true
                else:
                    checkList[1] += 1  # false

                del esaCallList[0]

            # ゴミエナジーの計算
            gomiEnergy.append(int(checkList[0] / sum(checkList) * 10))
            await ctx.send("ごちそうさま！現在のゴミエナジーは " + str(sum(gomiEnergy)))
            workEatList.remove(0)
            await ctx.send("正誤判定" + str(checkList))
            await ctx.send("食えたゴミ率" + str(checkList[0] / sum(checkList) * 100))
            print("ごちそうさま！現在のゴミエナジーは ", checkList[0])
            print("正誤判定", checkList)
        elif gomiWeekList[6 - len(dayCnt)] == 5:
            await ctx.send("今日はゴミ回収、無い日だよ〜")
    else:
        await ctx.send("食べられるものが無いよ〜、寝よう")


@bot.command()
async def start(ctx: commands.Context):
    if len(areaDict) > 1 and len(dayCnt) == 6:
        await ctx.send(
            "あなたの住んでる地域を選んでね！ （生田〜南生田）\n全部出てくるまで時間がかかるよ！待ってね！"
        )
        view = discord.ui.View()
        select_button = SelectButton(ctx.author)  # コマンドを呼んだユーザを渡す
        view.add_item(select_button)  # 作ったボタンを view に追加
        for i in areaDict.keys():
            await ctx.send(i, view=view)  # view と一緒にメッセージを送信
        await ctx.send("地域を選んでね！")
    else:
        await ctx.send("もう始まってるよ")


@bot.command()
async def status(ctx: commands.Context):

    await ctx.send(
        "### １週間、五味場 コウ を育ててね！\n### その日が何ゴミの回収日かによってエサとして与えなければいけないゴミが変わるよ！\n### エサに適さないゴミをdeleteボタンで削除しよう!"
    )
    await ctx.send(str(areaDict.keys()) + "地区のゴミ回収スケジュールは")
    j = 0
    for i in gomiWeekList:
        await ctx.send("> " + days[j] + gomiMatchDayDict[i])
        j += 1
    await ctx.send(
        "今日見つけるべきもの : " + gomiMatchDayDict[gomiWeekList[6 - len(dayCnt)]]
    )
    await ctx.send(
        "【コマンド一覧】\n- /esa : エサとなるゴミの召喚(1日1回)\n- /eat : 選別したエサのゴミを食べさせるよ\n- /next : 明日にするよ\n- /reset : 月曜日に戻るよ(地区はリセットされないよ)"
    )


@bot.command()
async def next(ctx: commands.Context):
    if (
        len(workEatList) == len(workEsaList)
        and len(dayCnt) > 1
        and len(workEsaList) == len(dayCnt) - 1
    ):
        await ctx.send("明日になったよ")
        dayCnt.remove(0)
        print("デー", len(dayCnt))
        todayGomi = gomiWeekList[6 - len(dayCnt)]
        await ctx.send("今日見つけるべきもの : " + gomiMatchDayDict[todayGomi])
        print("todayGomi", todayGomi)
        if todayGomi == 5:
            workEsaList.remove(0)
            workEatList.remove(0)
    elif len(dayCnt) == 1:
        # ここにend処理
        totalGomiEnergy = sum(gomiEnergy)
        if totalGomiEnergy <= 20:
            # バッド
            await ctx.send(
                "# 1週間が終わったよ\nあんたは分別をうまくできなかった。そうだろ？\nほら、見てみろよ。お前のペットはあんなに衰弱してる。\nかわいそうに。\n***神「お前は地獄行きだ」***\n\n### end.1 ペットをいじめた罪"
            )
        elif 21 <= totalGomiEnergy and totalGomiEnergy < 50:
            # 普通エンド
            await ctx.send(
                "# 1週間が終わったよ\n分別、そこそこできたじゃん。\nほら、見てみろよ。お前のペット\n一見健康体っぽいけど、ちょっと顔色悪いぜ？\nまぁ、ゴミを食うなんてそもそも馬鹿げた話さ。\n***神「まぁいいんじゃない？」***\n\n### end.2 可もなく不可もなく"
            )
        else:
            # 良いエンド
            await ctx.send(
                "# 1週間が終わったよ\nカンッペキだね！お前すごいよ。\nほら、見てみろよ。お前のペット！\nすごい元気だな！あんなに走り回って！...あ！？\nゴミ袋がそこら辺の枝に引っかかって破れた！？\n\n\n死、死んでる...\n***神「でもあいつは幸せだったと思うよ。」***\n\n### end3. 命はいずれ"
            )

        while len(dayCnt) < 6:
            dayCnt.append(0)
        while len(workEsaList) < 6:
            workEsaList.append(0)
        while len(workEatList) < 6:
            workEatList.append(0)

    else:
        await ctx.send("やり残したこと、あるんじゃない？")


@bot.command()
async def reset(ctx: commands.Context):
    while len(dayCnt) < 6:
        dayCnt.append(0)
    while len(workEsaList) < 6:
        workEsaList.append(0)
    while len(workEatList) < 6:
        workEatList.append(0)


# 起動時に動作する処理
@bot.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print("ログインしました")


bot.run(TOKEN)