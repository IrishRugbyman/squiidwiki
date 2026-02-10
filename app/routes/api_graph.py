"""API routes for graph data."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from app.database import get_db
from app.models.member import Member
from app.models.set import Set
from app.models.alliance import Alliance

router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/graph")
def get_graph_data(db: Session = Depends(get_db)):
    """Get graph data for visualization."""
    nodes = []
    edges = []
    
    # Add alliance nodes
    alliances = db.query(Alliance).all()
    for alliance in alliances:
        nodes.append({
            "id": f"alliance-{alliance.id}",
            "label": alliance.name,
            "type": "alliance",
            "group": "alliance",
            "size": 30
        })
    
    # Add set nodes
    sets = db.query(Set).all()
    for set_obj in sets:
        nodes.append({
            "id": f"set-{set_obj.id}",
            "label": set_obj.primary_name,
            "type": "set",
            "group": "set",
            "size": 20
        })
        
        # Add edge from set to alliance
        if set_obj.alliance_id:
            edges.append({
                "from": f"set-{set_obj.id}",
                "to": f"alliance-{set_obj.alliance_id}",
                "type": "alliance_member",
                "color": {"color": "#3b82f6"}
            })
        
        # Add ally edges
        for ally in set_obj.allies:
            # Only add one direction to avoid duplicates
            if set_obj.id < ally.id:
                edges.append({
                    "from": f"set-{set_obj.id}",
                    "to": f"set-{ally.id}",
                    "type": "ally",
                    "color": {"color": "#22c55e"}
                })
        
        # Add enemy edges
        for enemy in set_obj.enemies:
            # Only add one direction to avoid duplicates
            if set_obj.id < enemy.id:
                edges.append({
                    "from": f"set-{set_obj.id}",
                    "to": f"set-{enemy.id}",
                    "type": "enemy",
                    "color": {"color": "#ef4444"},
                    "dashes": True
                })
    
    # Add member nodes (limited to avoid clutter)
    members = db.query(Member).limit(100).all()
    for member in members:
        display_name = member.display_name
        nodes.append({
            "id": f"member-{member.id}",
            "label": display_name,
            "type": "member",
            "group": "member",
            "size": 10
        })
        
        # Add edge from member to set
        if member.set_id:
            edges.append({
                "from": f"member-{member.id}",
                "to": f"set-{member.set_id}",
                "type": "member_of",
                "color": {"color": "#6b7280"}
            })
        
        # Add edge from member to alliance (direct)
        if member.alliance_id:
            edges.append({
                "from": f"member-{member.id}",
                "to": f"alliance-{member.alliance_id}",
                "type": "alliance_member",
                "color": {"color": "#3b82f6"}
            })
    
    return {"nodes": nodes, "edges": edges}
