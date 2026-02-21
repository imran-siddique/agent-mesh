import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

# Configure Streamlit page
# Using wide layout for better visualization of network graphs
st.set_page_config(page_title="Trust Score Network Dashboard", layout="wide")

# Page title (kept plain text to avoid Unicode rendering issues)
st.title("Trust Score Network Dashboard")

st.markdown(
    """
    This dashboard visualizes a simple trust network graph between agents.
    Nodes represent agents and edges represent trust relationships.
    """
)

# ---------------------------
# Section: Create trust graph
# ---------------------------

# NOTE: Example demo data is hardcoded for simplicity.
# In production, this could be loaded from a file, database, or user input.
agents = ["Agent A", "Agent B", "Agent C", "Agent D", "Agent E"]
edges = [
    ("Agent A", "Agent B"),
    ("Agent A", "Agent C"),
    ("Agent B", "Agent D"),
    ("Agent C", "Agent D"),
    ("Agent D", "Agent E"),
]

# Build graph
G = nx.Graph()
G.add_nodes_from(agents)
G.add_edges_from(edges)

# ---------------------------------
# Section: Visualize graph in UI
# ---------------------------------

# Use dedicated matplotlib figure for Streamlit rendering
fig, ax = plt.subplots(figsize=(8, 6))

# Generate layout for consistent positioning
pos = nx.spring_layout(G, seed=42)

# Draw network graph
nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=2000,
    node_color="skyblue",
    font_size=10,
    font_weight="bold",
    edge_color="gray",
    ax=ax,
)

# Render figure in Streamlit
st.pyplot(fig)
