#!/usr/bin/env python3
"""Aggregate-only Taiwan Traditional Chinese locale gate for ASR outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


SIMPLIFIED_ONLY_CHARS = set(
    "个为义乌乐习乡书买乱争于亏云亚产亩亲亿仅从仑仓仪们价众优伙会伞伟传伤伪"
    "体余佣佥侠侣侥侦侧侨侩侪侬俣俦俨俩俪俭债倾偬偻偾偿傥傧储傩儿兑兖党"
    "兰关兴养兽冁内冈册写军农冯冲决况冻净凄准凉减凑凛几凤凫凭凯击凿刍划刘"
    "则刚创删别刬刭刹剂剐剑剥剧劝办务劢动励劲劳势勋勐勚匀匦匮区医华协单卖"
    "卢卤卫却厂厅历厉压厌厍厐厦厨厩县参双发变叙叠叶号叹叽吁后吓吕吗吣吨听"
    "启吴呐呒呓呕呖呗员呙呛呜咏咔咙咛咝咤响哑哒哓哔哕哗哙哜哝哟唛唠唡唢"
    "唤啧啬啭啮啰啴啸喷喽喾嗫嗳嘘嘤嘱噜噼嚣团园囱围囵国图圆圣圹场坂坏块"
    "坚坛坜坝坞坟坠垄垅垆垒垦垩垫垭垯垱垲垴埘埙埚埯堑堕塆墙壮声壳壶处备"
    "复够头夹夺奁奂奋奖奥妆妇妈妩妪妫姗姜娄娅娆娇娈娱娲娴婳婴婵婶媪嫒嫔嫱"
    "嬷孙学孪宁宝实宠审宪宫宽宾寝对寻导寿将尔尘尝尧尴尸尽层屉届属屡屦屿岁"
    "岂岖岗岘岙岚岛岭岳岽岿峃峡峣峤峥峦崂崃崭嵘嵚嵛嵝巅巩巯币帅师帏帐帘"
    "帜带帧帮帱帻帼幂庄庆庐庑库应庙庞废庼廪开异弃张弥弪弯弹强归当录彝彦彻"
    "径徕忆忏忧忾怀态怂怃怄怅怆怜总怼怿恋恳恶恸恹恺恻恼恽悦悫悬悭悯惊惧"
    "惨惩惫惬惭惮惯愍愠愤愦愿慑懑懒懔戆戋戏戗战戬户扎扑托执扩扪扫扬扰抚"
    "抛抟抠抡抢护报担拟拢拣拥拦拧拨择挂挚挛挜挝挞挟挠挡挢挣挤挥挦捞损捡换"
    "捣据掳掴掷掸掺揽揿搀搁搂搅携摄摅摆摇摈摊撄撑撵撷撸撺擞攒敌敛数斋斓"
    "斗斩断无旧时旷旸昙昼昽显晋晒晓晔晕晖暂暧术朴机杀杂权杆条来杨杩杰极构"
    "枞枢枣枥枧枨枪枫枭柜柠柽栀栅标栈栉栊栋栌栎栏树栖样栾桊桠桡桢档桤桥"
    "桦桧桨桩梦梼梾梿检棂椁椟椠椤椭楼榄榅榇榈榉槚槛槟槠横樯樱橥橱橹橼檩"
    "欢欤欧欲歼殁殇残殒殓殚殡殴毁毂毕毙毡毵氇气氢氩氲汇汉污汤汹沟没沣沤"
    "沥沦沧沨沩沪泞泪泶泷泸泺泻泼泽泾洁洒洼浃浅浆浇浈浊测浍济浏浐浑浒浓"
    "浔浕涂涌涛涝涞涟涠涡涢涣涤润涧涨涩淀渊渌渍渎渐渑渔渖渗温湾湿溃溅溆"
    "溇滗滚滞滟滠满滢滤滥滦滨滩滪漤潆潇潋潍潜潴澜濑濒灏灭灯灵灾灿炀炉炖"
    "炜炝点炼炽烁烂烃烛烟烦烧烨烩烫烬热焕焖焘煅煳熘爱爷牍牦牵牺犊状犷犸"
    "犹狈狞独狭狮狯狰狱狲猃猎猕猡猪猫猬献獭玑玛玮环现玱玺珉珏珐珑珰珲琏"
    "琐琼瑶瑷璎瓒瓯电画畅畴疖疗疟疠疡疬疮疯疱疴痈痉痒痖痨痪痫瘅瘆瘗瘘瘪"
    "瘫瘾瘿癞癣癫皑皱皲盏盐监盖盗盘眍眦眬着睁睐睑瞒瞩矫矶矾矿砀码砖砗砚"
    "砜砺砻砾础硁硕硖硗硚确硷碍碛碜碱礼祃祎祢祯祷祸禀禄禅离秃秆种积称秽"
    "秾稆税稣稳穑穷窃窍窑窜窝窥窦窭竖竞笃笋笔笕笺笼笾筑筚筛筜筝筹签简箓"
    "箦箧箨箩箪箫篑篓篮篱簖籁籴类籼粜粝粤粪粮糁糇紧絷纟纠纡红纣纤纥约级"
    "纨纩纪纫纬纭纯纰纱纲纳纵纶纷纸纹纺纽纾线绀绁绂练组绅细织终绉绊绋绌绍"
    "绎经绐绑绒结绔绕绖绗绘给绚绛络绝绞统绠绡绢绣绥绦继绩绪绫续绮绯绰绱绲"
    "绳维绵绶绷绸综绽绾绿缀缁缂缃缄缅缆缇缈缉缊缋缌缍缎缏缑缒缓缔缕编缗缘"
    "缙缚缛缜缝缟缠缡缢缣缤缥缦缧缨缩缪缫缬缭缮缯缰缱缲缳缴缵罂网罗罚罢"
    "罴羁羟羡翘翙翚耢耧耸耻聂聋职聍联聩聪肃肠肤肮肴肾肿胀胁胆胜胧胨胪胫"
    "胶脉脍脏脐脑脓脔脚脱脶脸腊腌腘腭腻腼腽腾膑臜舆舰舱艰艳艺节芈芗芜芦"
    "苁苇苈苋苌苍苎苏苧苹范茎茏茑茔茕茧荆荐荙荚荛荜荞荟荠荡荣荤荥荦荧荨"
    "荩荪荫荬荭荮药莅莱莲莳莴莶获莸莹莺莼萚萝萤营萦萧萨葱蒇蒉蒋蒌蓝蓟蓠"
    "蓣蓥蓦蔷蔹蔺蔼蕲蕴薮藓蘖虏虑虚虫虬虮虿虽虾虿蚀蚁蚂蚕蚬蛊蛎蛏蛮蛰蛱"
    "蛲蛳蛴蜕蜗蜡蝇蝈蝉蝎蝼蝾螀螨蟏衅衔补表衬衮袄袅袆袜袭袯装裆裈裢裤裣"
    "裥褛褴襁见观觃规觅视觇览觉觊觋觌觍觎觏觐觑觞触觯詟誉誊讠计订讣认讥"
    "讦讧讨让讪讫训议讯记讱讲讳讴讵讶讷许讹论讼讽设访诀证诂诃评诅识诈诉诊"
    "诋诌词诎诏译诒诓诔试诖诗诘诙诚诛诜话诞诟诠诡询诣诤该详诧诨诩诫诬语"
    "诮误诰诱诲诳说诵请诸诹诺读诼诽课诿谀谁谂调谄谅谆谈谊谋谌谍谎谏谐谑"
    "谒谓谔谕谖谗谘谙谚谛谜谝谞谟谠谡谢谣谤谥谦谧谨谩谪谫谬谭谮谯谰谱谲"
    "谳谴谵贝贞负贡财责贤败账货质贩贪贫贬购贮贯贰贱贲贳贴贵贷贸费贺贻贼贽"
    "贾贿赁赂赃资赅赆赇赈赉赊赋赌赍赎赏赐赓赔赖赘赙赚赛赜赝赞赠赡赢赣赵"
    "赶趋趱跃跄跞践跶跷跸跹跻踊踌踪踬踯蹑蹒蹰蹿躏躜躯车轧轨轩轫转轮软轰"
    "轱轲轳轴轵轶轷轸轹轺轻轼载轾轿辀辁辂较辄辅辆辇辈辉辊辋辍辎辏辐辑输"
    "辔辕辖辗辘辙辚辞辟辩辫边辽达迁过迈运还这进远违连迟迩迳迹适选逊递逦"
    "逻遗遥邓邝邬邮邹邺邻郁郏郑郓郦郧郸酂酝酦酱酽酾酿释里鉴銮錾钅钆钇针"
    "钉钊钋钌钍钎钏钐钑钒钓钔钕钗钙钚钛钜钝钞钟钠钡钢钣钤钥钦钧钨钩钪钫"
    "钬钭钮钯钰钱钲钳钴钵钶钷钸钹钺钻钼钽钾钿铀铁铂铃铄铅铆铈铉铊铋铌铍"
    "铎铐铑铒铕铖铗铘铙铛铜铝铞铟铠铡铢铣铤铥铧铨铩铪铫铬铭铮铯铰铱铲铳"
    "铴铵银铷铸铹铺铻铼铽链铿销锁锂锃锄锅锆锇锋锌锏锐锑锒锓锔锕锖锗错锚"
    "锛锜锝锞锟锠锡锢锣锤锥锦锨锩锫锬锭键锯锰锱锲锴锵锶锷锸锹锺锻锼锽锾"
    "锿镀镁镂镃镄镅镆镇镈镉镊镌镍镎镏镐镑镒镓镔镕镖镗镘镙镚镛镜镝镞镟镠"
    "镡镢镣镤镥镦镧镨镩镪镫镬镭镮镯镰镱镲镳镴长门闩闪闫闭问闯闰闱闲闳间"
    "闵闶闷闸闹闺闻闼闽闾阀阁阂阃阅阆阇阈阉阊阋阌阍阎阏阐阑阒阔阕阖阗阙"
    "阚队阳阴阵阶际陆陇陈陉陕陧陨险随隐隶隽难雏雠雳雾霁霉靓静靥鞑鞒鞯韦"
    "韧韨韩韪韫韬韵页顶顷顸项顺须顼顽顾顿颀颁颂预颅领颇颈颉颊颋颌颍颏颐"
    "频颓颔颖颗题颚颛颜额颞颟颠颡颢颤颥颦风飏飐飒飓飔飕飖飘飙飚飞飨餍饣"
    "饥饧饨饩饪饫饬饭饮饯饰饱饲饳饴饵饶饷饸饹饺饻饼饽饿馀馁馂馃馄馅馆馇"
    "馈馉馊馋馌馍馏馐馑馒馓馔馕马驭驮驯驰驱驳驴驶驷驸驹驻驼驽驾驿骀骁骂"
    "骄骅骆骇骈骉骊骋验骍骎骏骐骑骒骓骖骗骘骙骚骛骜骝骞骟骠骡骢骣骤骥骧"
    "髅髋髌鬓魇魉鱼鱿鲁鲂鲅鲆鲇鲈鲋鲍鲎鲐鲑鲒鲔鲕鲚鲛鲜鲝鲞鲟鲠鲡鲢鲣鲤"
    "鲥鲦鲧鲨鲩鲪鲫鲬鲭鲮鲰鲱鲲鲳鲴鲵鲶鲷鲸鲺鲻鲼鲽鲾鳀鳃鳄鳅鳆鳇鳊鳋鳌"
    "鳍鳎鳏鳐鳓鳔鳕鳖鳗鳘鳙鳜鳝鳞鳟鳠鳡鳢鸟鸠鸡鸢鸣鸥鸦鸧鸨鸩鸪鸫鸬鸭"
    "鸮鸯鸰鸱鸲鸳鸵鸶鸷鸸鸹鸺鸽鸾鸿鹁鹂鹃鹄鹅鹆鹇鹈鹉鹊鹋鹌鹏鹐鹑鹕鹗"
    "鹘鹚鹛鹜鹞鹟鹠鹡鹢鹣鹤鹥鹦鹧鹨鹩鹪鹫鹬鹭鹰鹱鹲鹳鹴鹾麦麸黄黉黡黩"
    "黪鼋鼍齐齑齿龀龁龂龄龅龆龇龈龉龊龋龌龙龚龛龟"
)

TIMESTAMP_RE = re.compile(r"(?:\b\d{1,2}:\d{2}(?::\d{2})?\b|\[\s*\d+(?:\.\d+)?\s*[-~]\s*\d+(?:\.\d+)?\s*\])")
SPEAKER_RE = re.compile(r"(speaker\s*\d+|speaker\s*[ab]|說話者\s*[一二三四五六七八九十\d]+|客服[:：]|客戶[:：])", re.IGNORECASE)
ASCII_ALPHA_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
SENSITIVE_KEYS = {
    "audio_id",
    "sample_id",
    "reference_text",
    "hypothesis_text",
    "pred_text",
    "asr_hypotheses_json",
    "reviewer_notes",
}


def read_rows(path: Path, fmt: str) -> list[dict[str, Any]]:
    if fmt == "auto":
        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            fmt = "jsonl"
        elif suffix == ".json":
            fmt = "json"
        elif suffix == ".tsv":
            fmt = "tsv"
        elif suffix == ".csv":
            fmt = "csv"
        else:
            raise ValueError(f"cannot infer input format for {path}")

    if fmt == "jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if fmt == "json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return payload["rows"]
        raise ValueError("json input must be a list or contain a rows list")
    if fmt in {"tsv", "csv"}:
        delimiter = "\t" if fmt == "tsv" else ","
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle, delimiter=delimiter))
    raise ValueError(f"unsupported input format: {fmt}")


def row_stats(text: str) -> dict[str, Any]:
    cjk_chars = CJK_RE.findall(text)
    simplified = [char for char in cjk_chars if char in SIMPLIFIED_ONLY_CHARS]
    has_text = bool(text.strip())
    has_cjk = bool(cjk_chars)
    english_only = has_text and not has_cjk and bool(ASCII_ALPHA_RE.search(text))
    timestamp_like = bool(TIMESTAMP_RE.search(text))
    speaker_label_like = bool(SPEAKER_RE.search(text))
    locale_violation = bool(simplified) or english_only or timestamp_like or speaker_label_like
    return {
        "has_text": has_text,
        "cjk_char_count": len(cjk_chars),
        "simplified_char_count": len(simplified),
        "simplified_char_rate": (len(simplified) / len(cjk_chars)) if cjk_chars else 0.0,
        "english_only": english_only,
        "timestamp_like": timestamp_like,
        "speaker_label_like": speaker_label_like,
        "locale_violation": locale_violation,
    }


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "input_path",
        "rows",
        "expected_rows",
        "valid_output_rate",
        "simplified_char_count",
        "simplified_char_rate",
        "locale_violation_rows",
        "locale_violation_rate",
        "english_only_rows",
        "timestamp_like_rows",
        "speaker_label_like_rows",
        "locale_gate_passed",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def aggregate(
    *,
    input_paths: list[Path],
    text_field: str,
    input_format: str,
    expected_rows: int | None,
    max_locale_violation_rate: float,
    max_simplified_char_rate: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started = time.time()
    per_file: list[dict[str, Any]] = []
    totals = {
        "rows": 0,
        "valid_output_rows": 0,
        "cjk_char_count": 0,
        "simplified_char_count": 0,
        "locale_violation_rows": 0,
        "english_only_rows": 0,
        "timestamp_like_rows": 0,
        "speaker_label_like_rows": 0,
    }

    for input_path in input_paths:
        rows = read_rows(input_path, input_format)
        file_stats = {
            "input_path": str(input_path),
            "rows": len(rows),
            "valid_output_rows": 0,
            "cjk_char_count": 0,
            "simplified_char_count": 0,
            "locale_violation_rows": 0,
            "english_only_rows": 0,
            "timestamp_like_rows": 0,
            "speaker_label_like_rows": 0,
        }
        for row in rows:
            stats = row_stats(str(row.get(text_field, "") or ""))
            file_stats["valid_output_rows"] += int(stats["has_text"])
            file_stats["cjk_char_count"] += stats["cjk_char_count"]
            file_stats["simplified_char_count"] += stats["simplified_char_count"]
            file_stats["locale_violation_rows"] += int(stats["locale_violation"])
            file_stats["english_only_rows"] += int(stats["english_only"])
            file_stats["timestamp_like_rows"] += int(stats["timestamp_like"])
            file_stats["speaker_label_like_rows"] += int(stats["speaker_label_like"])

        for key in totals:
            totals[key] += file_stats[key]

        expected = expected_rows if expected_rows is not None else len(rows)
        simplified_rate = (
            file_stats["simplified_char_count"] / file_stats["cjk_char_count"]
            if file_stats["cjk_char_count"]
            else 0.0
        )
        violation_rate = file_stats["locale_violation_rows"] / max(len(rows), 1)
        valid_output_rate = file_stats["valid_output_rows"] / max(expected, 1)
        file_stats.update(
            {
                "expected_rows": expected,
                "valid_output_rate": round(valid_output_rate, 6),
                "simplified_char_rate": round(simplified_rate, 6),
                "locale_violation_rate": round(violation_rate, 6),
                "locale_gate_passed": (
                    valid_output_rate >= 0.95
                    and simplified_rate <= max_simplified_char_rate
                    and violation_rate <= max_locale_violation_rate
                ),
            }
        )
        per_file.append(file_stats)

    expected_total = expected_rows if expected_rows is not None and len(input_paths) == 1 else totals["rows"]
    valid_output_rate = totals["valid_output_rows"] / max(expected_total, 1)
    simplified_rate = (
        totals["simplified_char_count"] / totals["cjk_char_count"]
        if totals["cjk_char_count"]
        else 0.0
    )
    violation_rate = totals["locale_violation_rows"] / max(totals["rows"], 1)
    passed = (
        valid_output_rate >= 0.95
        and simplified_rate <= max_simplified_char_rate
        and violation_rate <= max_locale_violation_rate
    )
    payload = {
        "ok": passed,
        "status": "locale_gate_passed" if passed else "locale_gate_failed",
        "input_boundary": "prediction files only; output is aggregate-only locale counts",
        "output_boundary": "no transcript, hypothesis text, audio IDs, sample IDs, reviewer notes, or raw rows emitted",
        "text_field": text_field,
        "expected_rows": expected_total,
        "rows": totals["rows"],
        "valid_output_rows": totals["valid_output_rows"],
        "valid_output_rate": round(valid_output_rate, 6),
        "simplified_char_count": totals["simplified_char_count"],
        "cjk_char_count": totals["cjk_char_count"],
        "simplified_char_rate": round(simplified_rate, 6),
        "locale_violation_rows": totals["locale_violation_rows"],
        "locale_violation_rate": round(violation_rate, 6),
        "english_only_rows": totals["english_only_rows"],
        "timestamp_like_rows": totals["timestamp_like_rows"],
        "speaker_label_like_rows": totals["speaker_label_like_rows"],
        "thresholds": {
            "min_valid_output_rate": 0.95,
            "max_locale_violation_rate": max_locale_violation_rate,
            "max_simplified_char_rate": max_simplified_char_rate,
        },
        "promotion_decision": (
            "eligible_for_next_gate"
            if passed
            else "do_not_promote_until_raw_locale_gate_passes_or_audited_repair_lane_is_approved"
        ),
        "per_file": per_file,
        "runtime_seconds": round(time.time() - started, 4),
    }
    serialized = json.dumps(payload, ensure_ascii=False)
    for key in SENSITIVE_KEYS:
        if key in serialized and key != text_field:
            raise ValueError(f"sensitive key leaked into aggregate output: {key}")
    return payload, per_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--text-field", default="hypothesis_text")
    parser.add_argument("--format", choices=["auto", "jsonl", "json", "tsv", "csv"], default="auto")
    parser.add_argument("--expected-rows", type=int)
    parser.add_argument("--max-locale-violation-rate", type=float, default=0.01)
    parser.add_argument("--max-simplified-char-rate", type=float, default=0.0)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-tsv", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, per_file = aggregate(
        input_paths=args.input,
        text_field=args.text_field,
        input_format=args.format,
        expected_rows=args.expected_rows,
        max_locale_violation_rate=args.max_locale_violation_rate,
        max_simplified_char_rate=args.max_simplified_char_rate,
    )
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.output_tsv:
        write_tsv(args.output_tsv, per_file)
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "rows": payload["rows"],
                "locale_violation_rows": payload["locale_violation_rows"],
                "simplified_char_count": payload["simplified_char_count"],
                "promotion_decision": payload["promotion_decision"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
