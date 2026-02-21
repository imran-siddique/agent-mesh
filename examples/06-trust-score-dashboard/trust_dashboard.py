import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="Trust Score Network Dashboard", layout="wide")

st.title("🔗 Trust Score Network Dashboard")

st.markdown(
    """
    This dashboard visualizes a simple trust network graph between agents.
    Nodes represent agents and edges represent trust relationships.
    """
)

# Create a sample trust network graph
G = nx.Graph()

# Add nodes (agents)
agents = ["Agent A", "Agent B", "Agent C", "Agent D", "Agent E"]
G.add_nodes_from(agents)

# Add trust edges (relationships)
edges = [
    ("Agent A", "Agent B"),
    ("Agent A", "Agent C"),
    ("Agent B", "Agent D"),
    ("Agent C", "Agent D"),
    ("Agent D", "Agent E"),
]

G.add_edges_from(edges)

# Draw graph
plt.figure(figsize=(8, 6))
pos = nx.spring_layout(G, seed=42)
nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=2000,
    node_color="skyblue",
    font_size=10,
    font_weight="bold",
    edge_color="gray",
)

st.pyplot(plt)
