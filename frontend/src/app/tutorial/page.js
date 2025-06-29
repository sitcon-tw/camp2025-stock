export default function TutorialPage() {
    return (
        <div className="min-h-screen bg-[#0f203e] pb-32">
            <div className="container mx-auto max-w-4xl px-8 py-8">
                <h1 className="mb-8 text-center text-3xl font-bold text-[#82bee2]">
                    📈 SITC 股市交易指南
                </h1>

                <div className="mb-8 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="text-md text-white">
                        歡迎來到 SITCON Camp 的 SITC
                        模擬股市！你可以使用「營隊點數」來體驗
                        投資的樂趣，就算你從沒碰過股票也沒關係！
                    </p>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    TL;DR
                </h2>
                <ul className="mb-8 list-disc pl-6 text-white">
                    <li>低買高賣。</li>
                    <li>點少的輸，點多的贏。</li>
                </ul>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🧩 基本玩法總覽
                </h2>
                <div className="mb-8 overflow-x-auto">
                    <table className="w-full overflow-hidden">
                        <thead className="border-b border-[#82bee2] [&>tr>th]:bg-[#19325e] [&>tr>th:not(:last-child)]:border-r [&>tr>th:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <th className="rounded-tl-xl px-4 py-2 text-left text-[#82bee2]">
                                    項目
                                </th>
                                <th className="rounded-tr-xl px-4 py-2 text-left text-[#82bee2]">
                                    說明
                                </th>
                            </tr>
                        </thead>
                        <tbody className="[&>tr:not(:last-child)>td]:border-b [&>tr:not(:last-child)>td]:border-[#82bee2] [&>tr>td]:bg-[#1a2e4a] [&>tr>td:not(:last-child)]:border-r [&>tr>td:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    交易單位
                                </td>
                                <td className="px-4 py-2 text-white">
                                    使用「營隊點數」購買或賣出「SITC
                                    股票」
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    操作方式
                                </td>
                                <td className="px-4 py-2 text-white">
                                    所有買賣都用 Telegram bot
                                    下指令完成
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    資訊查詢
                                </td>
                                <td className="px-4 py-2 text-white">
                                    用網頁查詢目前價格、交易紀錄等資訊
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    交易時間
                                </td>
                                <td className="px-4 py-2 text-white">
                                    只在指定時段能交易（如活動時可能會禁止）
                                </td>
                            </tr>
                            <tr>
                                <td className="rounded-bl-xl px-4 py-2 text-white">
                                    點數排行榜
                                </td>
                                <td className="rounded-br-xl px-4 py-2 text-white">
                                    以組別或個人為單位，可將股票換算點數
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    📱 操作流程總覽
                </h2>
                <div className="mb-6 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="font-semibold text-[#82bee2]">
                        所有交易指令都透過 Telegram Bot 完成！
                    </p>
                </div>

                <p className="mb-6 text-white">你可以選擇：</p>
                <ol className="mb-8 list-decimal pl-6 text-white">
                    <li>
                        即時交易（市價單） →
                        直接成交（人家想賣多少就用多少買）
                    </li>
                    <li>
                        掛單交易（限價單） →
                        等待有人來成交（等到你要的價格）
                    </li>
                </ol>

                <div className="mb-8 rounded-lg bg-[#0d2543] border border-[#82bee2] p-6">
                    <h3 className="mb-4 text-xl font-semibold text-[#82bee2]">
                        ⚡ 即時成交機制說明
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <h4 className="mb-2 font-semibold text-[#a8d4f0]">市價單即時成交：</h4>
                            <ul className="list-disc pl-6 text-white space-y-1">
                                <li><strong>市價買單</strong>：優先與最低價賣單配對，若無賣單則從 IPO 以 20 點/股購買</li>
                                <li><strong>市價賣單</strong>：優先與最高價買單配對，若無買單則拒絕交易</li>
                                <li>成交立即執行，無需等待</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="mb-2 font-semibold text-[#a8d4f0]">限價單可能即時成交：</h4>
                            <ul className="list-disc pl-6 text-white space-y-1">
                                <li><strong>限價買單</strong>：當有賣單價格 ≤ 你的買價時，透過撮合系統立即成交</li>
                                <li><strong>限價賣單</strong>：當有買單價格 ≥ 你的賣價時，透過撮合系統立即成交</li>
                                <li>撮合系統每 60 秒執行一次，或在下單後觸發</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="mb-2 font-semibold text-[#a8d4f0]">IPO 回補機制：</h4>
                            <ul className="list-disc pl-6 text-white space-y-1">
                                <li>當市場缺乏賣單時，市價買單可從系統 IPO 購買</li>
                                <li>IPO 價格固定為 20 點/股，提供市場流動性</li>
                                <li>IPO 股數有限，售完後市價買單可能失敗</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🛒 如何「買股票」？
                </h2>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    ✅ 即時買（市價買入）
                </h3>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /stock
                    </code>
                </div>
                <div className="mb-6">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>
                            使用 /stock
                            指令進入交易介面，選擇市價買入。
                        </li>
                        <li>用當下市場「賣一價」直接買入，若無賣單則從 IPO 以 20 點/股購買。</li>
                        <li>
                            系統會顯示「你花了多少點數，買了幾張」。
                        </li>
                        <li><span className="text-[#ffd700]">立即成交</span>：無需等待撮合時間。</li>
                    </ul>
                </div>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    ✅ 掛單買（限價掛單）
                </h3>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /stock
                    </code>
                </div>
                <div className="mb-8">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>
                            使用 /stock
                            指令進入交易介面，選擇限價掛單買入。
                        </li>
                        <li>掛在市場等人賣給你。</li>
                        <li>
                            只有當「有人的賣價 ≤
                            你的買價」時才會成交。
                        </li>
                        <li><span className="text-[#ffd700]">可能即時成交</span>：若有符合條件的賣單，透過撮合系統立即配對。</li>
                    </ul>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    💰 如何「賣股票」？
                </h2>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    ✅ 即時賣（市價賣出）
                </h3>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /stock
                    </code>
                </div>
                <div className="mb-6">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>
                            使用 /stock
                            指令進入交易介面，選擇市價賣出。
                        </li>
                        <li>以當下市場「買一價」賣出。</li>
                        <li>越多競爭者願意買，價格越好。</li>
                        <li><span className="text-[#ffd700]">立即成交</span>：若有買單則立即配對，無買單則拒絕交易。</li>
                    </ul>
                </div>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    ✅ 掛單賣（限價掛單）
                </h3>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /stock
                    </code>
                </div>
                <div className="mb-8">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>
                            使用 /stock
                            指令進入交易介面，選擇限價掛單賣出。
                        </li>
                        <li>掛單等待市場出價。</li>
                        <li>
                            只有當「有人的買價 ≥
                            你的賣價」時才會成交。
                        </li>
                        <li><span className="text-[#ffd700]">可能即時成交</span>：若有符合條件的買單，透過撮合系統立即配對。</li>
                    </ul>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    💸 如何「轉帳」？
                </h2>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /transfer
                    </code>
                </div>
                <div className="mb-8">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>可以轉點數給其他人。</li>
                        <li>會抽取 5% 手續費。</li>
                    </ul>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🔍 如何「查看小隊點數」？
                </h2>
                <div className="mb-4 rounded-lg bg-[#1a2e4a] p-4">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📩 指令格式：
                    </p>
                    <code className="rounded bg-black px-2 py-1 text-green-400">
                        /point
                    </code>
                </div>
                <div className="mb-8">
                    <p className="mb-2 font-semibold text-[#82bee2]">
                        📌 說明：
                    </p>
                    <ul className="list-disc pl-6 text-white">
                        <li>查看自己小隊的總點數。</li>
                    </ul>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    📊 如何查詢市場價格？
                </h2>
                <p className="mb-4 text-white">網頁會顯示：</p>
                <div className="mb-8 overflow-x-auto">
                    <table className="w-full overflow-hidden">
                        <thead className="border-b border-[#82bee2] [&>tr>th]:bg-[#19325e] [&>tr>th:not(:last-child)]:border-r [&>tr>th:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <th className="rounded-tl-xl px-4 py-2 text-left text-[#82bee2]">
                                    項目
                                </th>
                                <th className="rounded-tr-xl px-4 py-2 text-left text-[#82bee2]">
                                    說明
                                </th>
                            </tr>
                        </thead>
                        <tbody className="[&>tr:not(:last-child)>td]:border-b [&>tr:not(:last-child)>td]:border-[#82bee2] [&>tr>td]:bg-[#1a2e4a] [&>tr>td:not(:last-child)]:border-r [&>tr>td:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    買一價 / 賣一價
                                </td>
                                <td className="px-4 py-2 text-white">
                                    市場目前最高買價 / 最低賣價
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    即時價格
                                </td>
                                <td className="px-4 py-2 text-white">
                                    近五筆成交平均價格
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    今日漲跌
                                </td>
                                <td className="px-4 py-2 text-white">
                                    與開盤價相比的變動
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    今日最低 / 最高
                                </td>
                                <td className="px-4 py-2 text-white">
                                    單日內波動範圍
                                </td>
                            </tr>
                            <tr>
                                <td className="rounded-bl-xl px-4 py-2 text-white">
                                    最近成交紀錄
                                </td>
                                <td className="rounded-br-xl px-4 py-2 text-white">
                                    顯示價格與成交時間
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🕒 交易時間？
                </h2>
                <p className="mb-8 text-white">
                    每天限定時段可交易，可在網站首頁查看。
                </p>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🏆 排行榜怎麼算？
                </h2>
                <p className="mb-4 text-white">
                    想知道你現在是營隊的投資之神嗎？排行榜幫你算清楚！
                </p>

                <h3 className="mb-3 text-xl font-semibold text-[#82bee2]">
                    排行榜會顯示兩種資產總值：
                </h3>
                <div className="mb-8 overflow-x-auto">
                    <table className="w-full overflow-hidden">
                        <thead className="border-b border-[#82bee2] [&>tr>th]:bg-[#19325e] [&>tr>th:not(:last-child)]:border-r [&>tr>th:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <th className="rounded-tl-xl px-4 py-2 text-left text-[#82bee2]">
                                    類型
                                </th>
                                <th className="rounded-tr-xl px-4 py-2 text-left text-[#82bee2]">
                                    說明
                                </th>
                            </tr>
                        </thead>
                        <tbody className="[&>tr:not(:last-child)>td]:border-b [&>tr:not(:last-child)>td]:border-[#82bee2] [&>tr>td]:bg-[#1a2e4a] [&>tr>td:not(:last-child)]:border-r [&>tr>td:not(:last-child)]:border-[#82bee2]">
                            <tr>
                                <td className="px-4 py-2 text-white">
                                    評價資產
                                </td>
                                <td className="px-4 py-2 text-white">
                                    點數 + 股票市值（用當下價格估算）
                                </td>
                            </tr>
                            <tr>
                                <td className="rounded-bl-xl px-4 py-2 text-white">
                                    現金資產
                                </td>
                                <td className="rounded-br-xl px-4 py-2 text-white">
                                    只看實際點數（未賣股票不算）
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <h2 className="mb-4 text-2xl font-bold text-[#82bee2]">
                    🧠 常見問題（FAQ）
                </h2>

                <div className="space-y-6">
                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 如果我買不到怎麼辦？
                        </h3>
                        <p className="text-white">
                            你可能買的價格太低，請改用市價單或調整掛單價格。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 股票價格怎麼決定？
                        </h3>
                        <p className="text-white">看你要賣多少錢。</p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 如果今天沒人跟我成交，怎麼辦？
                        </h3>
                        <p className="text-white">
                            掛著等，或是取消再下其他價格。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 股票有分紅嗎？
                        </h3>
                        <p className="text-white">沒有。</p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 我可以轉點數給別人嗎？
                        </h3>
                        <p className="text-white">
                            可以。使用 /transfer 指令，會抽取 5%
                            手續費。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 如果掛單之後我沒點數了怎麼辦？
                        </h3>
                        <p className="text-white">會自動取消。</p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓ 即時股價如何計算？
                        </h3>
                        <p className="text-white">
                            根據最後五筆的平均成交價。
                        </p>
                    </div>

                    <div>
                        <h3 className="mb-2 text-lg font-semibold text-[#82bee2]">
                            ❓
                            我只要開一個很高的單是不是股價就上去了？
                        </h3>
                        <p className="text-white">
                            對。但前提是有人要買。
                        </p>
                        <p className="text-white">
                            如果你持有的股票很多的話確實容易控制股價。
                        </p>
                    </div>
                </div>

                {/* <div className="mt-8 overflow-hidden rounded-xl bg-[#1a2e4a] p-3">
                    <blockquote className="text-center text-lg text-[#82bee2] italic">
                        最大的秘密，就是票多的贏、票少的輸。 -韓國瑜
                    </blockquote>
                </div> */}
            </div>
        </div>
    );
}
