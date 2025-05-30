function RankingItem({ rank, name }) {
    return (
        <div className="bg-[#19325e] flex w-full max-w-2xl rounded-xl p-3 items-center">
            <span className="text-[#82bee2] font-bold mr-4">{rank}.</span>
            <h3 className="text-lg font-semibold text-[#82bee2]">{name}</h3>
        </div>
    );
}

function RankingList({ title, items }) {
    return (
        <>
            <h2 className="text-xl font-bold text-[#82bee2] my-3 mt-8">
                {title}
            </h2>
            <div className="flex gap-5 flex-col justify-center items-center mt-2">
                {items.map((item, index) => (
                    <RankingItem
                        key={index}
                        rank={item.rank}
                        name={item.name}
                    />
                ))}
            </div>
        </>
    );
}

export default function Dash() {
    // 組排行
    const groupRankings = [
        { rank: 1, name: "個人名稱" },
        { rank: 2, name: "個人名稱" },
        { rank: 3, name: "個人名稱" },
        { rank: 4, name: "個人名稱" },
    ];

    // 個人排行
    const personalRankings = [
        { rank: 1, name: "個人名稱" },
        { rank: 2, name: "個人名稱" },
        { rank: 3, name: "個人名稱" },
        { rank: 4, name: "個人名稱" },
        { rank: 5, name: "個人名稱" },
        { rank: 5, name: "個人名稱" },
    ];

    return (
        <div className="bg-[#0f203e] min-h-screen items-center justify-center pb-36">
            <div className="flex flex-col h-screen px-8">
                <h2 className="text-3xl font-bold text-[#82bee2] mx-auto mt-10 mb-5">
                    排行榜
                </h2>

                <RankingList title="組排行" items={groupRankings} />

                <RankingList title="個人排行" items={personalRankings} />
            </div>
        </div>
    );
}