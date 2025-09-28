from openai import OpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans


client = OpenAI(api_key="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")

articles = [
    # 1. Reuters – SCO summit in China (Reuters)
    """SCO summit 2025 as it happened: China's Xi met Putin and Modi, as Trump's shadow loomed — Chinese President Xi Jinping hosted the Shanghai Cooperation Organisation summit in Tianjin, joined by leaders Vladimir Putin and Narendra Modi. Xi pressed for a new global security and economic order that elevates the interests of the Global South, criticizing U.S. tariff policies and hegemony. The summit underscored shifting geopolitical alignments as leaders navigated regional and global tensions, with economic integration and defense alliance discussions taking place behind closed doors.""",

    # 2. Reuters – Venezuela regime change accusation (same news outlet)
    """Venezuela's Maduro says US seeking regime change with naval build-up — In a rare press conference, Venezuelan President Nicolás Maduro accused the United States of attempting regime change via a U.S. naval buildup in the Southern Caribbean. Tensions have heightened with increased deployments by the U.S., which officials say target drug cartel threats, while Maduro framed the move as an act of aggression against a sovereign nation in the region.""",

    # 3. Reuters – Trump says India offered to reduce tariffs (another Reuters story)
    """Trump says India offered to reduce tariffs on U.S. goods to zero — President Trump claimed that India offered to eliminate tariffs on U.S. exports during bilateral talks, signaling warming trade ties. Indian Prime Minister Modi's presence at the SCO summit illustrated multi-polar diplomacy, even as U.S. trade officials weighed the impact of reduced duties on American industries.""",

    # 4. Reuters – Chicago protests against federal intervention
    """In Chicago, thousands protest against threat of ICE, National Guard deployment — Thousands gathered in downtown Chicago to protest President Trump's threats to deploy federal immigration agents and National Guard troops. Demonstrators called the proposal unnecessary and an overstep by the federal government, with chants and signs emphasizing city autonomy and civil rights.""",

    # 5. Reuters – Putin demands NATO enlargement be addressed
    """After talks with Xi and Modi, Putin says NATO enlargement has to be addressed for Ukraine peace — Following high-level talks, Russian President Putin argued that NATO's eastward expansion must be considered to achieve lasting peace in Ukraine. The comment came amid the SCO summit context and was portrayed as Moscow pushing for security assurances in a reshaping geopolitical landscape.""",

    # 6. Reuters – Trump administration proposed Education Department shutdown (legal/government)
    """Trump to sign order to shut down Department of Education, White House says — President Trump plans to issue an executive order aimed at dismantling the U.S. Department of Education, directing education authority back to the states. The move drew criticism from civil rights groups and Democratic lawmakers, who argue the action would jeopardize federal support for K-12 and higher education.""",

    # 7. Fox News – Burning Man homicide story (Fox)
    """Burning Man guest found in 'pool of blood' in suspected homicide at climax of wild desert festival, sheriff says — A guest at the Burning Man festival in Nevada was discovered dead in a pool of blood during the festival’s finale, and authorities are investigating the death as a homicide. Participants remain under investigation and a perimeter has been established near the makeshift campsites.""",

    # 8. Fox News – Chicago shootings coverage (Fox)
    """Chicago shootings leave at least 7 dead, dozens more injured as city insists it doesn't need Trump's help — At least seven people were killed and dozens injured in Chicago over Labor Day weekend. Mayor Brandon Johnson has issued an executive order barring cooperation with federal forces like the National Guard, rejecting Trump's proposal to send law enforcement into the city.""",

    # 9. Fox News – Sports highlight: CJ Daniels catch
    """Miami's CJ Daniels makes insane one-handed touchdown catch in win over Notre Dame — Miami Hurricanes wide receiver CJ Daniels pulled off a spectacular one-handed touchdown snag in a tight win against Notre Dame. The catch is already being hailed as a top play of the college football season, thrilling fans and sports analysts alike.""",

    # 10. Fox News – Human plague case in New Mexico
    """Human plague case reported; patient likely exposed while camping — New Mexico health officials confirmed the first human case of plague in 2025 in a 43-year-old man from Valencia County. The patient, now discharged, likely contracted the illness while camping in Rio Arriba County. Officials reminded the public that plague remains endemic in wildlife and prevention remains key.""",
]

# -----------------------------
# 3) Get embeddings
# -----------------------------
embeddings = []
for text in articles:
    resp = client.embeddings.create(
        model="text-embedding-3-small",  # or "text-embedding-3-large" for higher accuracy
        input=text
    )
    embeddings.append(resp.data[0].embedding)

embeddings = np.array(embeddings)

sim_matrix = cosine_similarity(embeddings)

# 2. Set threshold (tweak this!)
threshold = 0.65

# 3. Build adjacency list
n = len(articles)
adj = {i: set() for i in range(n)}
for i in range(n):
    for j in range(i+1, n):
        if sim_matrix[i][j] >= threshold:
            adj[i].add(j)
            adj[j].add(i)

# 4. DFS to find connected groups
visited = set()
groups = []
for i in range(n):
    if i in visited:
        continue
    stack = [i]
    comp = []
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        comp.append(node)
        for nei in adj[node]:
            if nei not in visited:
                stack.append(nei)
    groups.append(comp)

# 5. Print groups with article text
print("\n=== Threshold-based groups ===")
for gidx, g in enumerate(groups):
    print(f"Group {gidx}:")
    for idx in g:
        print(f"  - Article {idx}")