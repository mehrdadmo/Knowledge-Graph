#!/usr/bin/env python3
"""
Knowledge Graph Sync CLI
Command-line interface for syncing PostgreSQL data to Neo4j knowledge graph
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from loguru import logger
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_graph_sync import KnowledgeGraphSync
from config import settings

app = typer.Typer(help="Logistics Knowledge Graph Sync CLI")
console = Console()


def setup_logging():
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level=settings.log_level
    )


@app.command()
def init():
    """Initialize the Neo4j graph with constraints"""
    setup_logging()
    console.print(Panel("Initializing Knowledge Graph", style="bold blue"))
    
    try:
        sync = KnowledgeGraphSync()
        sync.initialize_graph()
        console.print("✅ Graph initialized successfully!", style="bold green")
    except Exception as e:
        console.print(f"❌ Error initializing graph: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def sync(
    all: bool = typer.Option(False, "--all", "-a", help="Sync all data"),
    document_id: int = typer.Option(None, "--document", "-d", help="Sync specific document ID")
):
    """Sync data from PostgreSQL to Neo4j"""
    setup_logging()
    
    if not all and not document_id:
        console.print("❌ Please specify either --all or --document <id>", style="bold red")
        raise typer.Exit(1)
    
    try:
        sync = KnowledgeGraphSync()
        
        if all:
            console.print(Panel("Syncing All Data", style="bold blue"))
            sync.sync_all_data()
            console.print("✅ All data synced successfully!", style="bold green")
        else:
            console.print(Panel(f"Syncing Document {document_id}", style="bold blue"))
            sync.sync_single_document(document_id)
            console.print(f"✅ Document {document_id} synced successfully!", style="bold green")
    
    except Exception as e:
        console.print(f"❌ Error during sync: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def status():
    """Show sync status and graph statistics"""
    setup_logging()
    
    try:
        sync = KnowledgeGraphSync()
        status_data = sync.get_sync_status()
        
        # PostgreSQL Statistics
        pg_table = Table(title="PostgreSQL Statistics", show_header=True, header_style="bold magenta")
        pg_table.add_column("Entity", style="cyan")
        pg_table.add_column("Count", justify="right", style="green")
        
        for entity, count in status_data["postgresql"].items():
            pg_table.add_row(entity.replace("_", " ").title(), str(count))
        
        console.print(pg_table)
        console.print()
        
        # Neo4j Statistics
        neo4j_table = Table(title="Neo4j Statistics", show_header=True, header_style="bold magenta")
        neo4j_table.add_column("Node Type", style="cyan")
        neo4j_table.add_column("Count", justify="right", style="green")
        
        for node_type, count in status_data["neo4j"].items():
            if node_type != "relationships":
                neo4j_table.add_row(node_type.replace("_", " ").title(), str(count))
        
        console.print(neo4j_table)
        console.print()
        
        # Relationship Statistics
        if "relationships" in status_data["neo4j"] and status_data["neo4j"]["relationships"]:
            rel_table = Table(title="Relationship Statistics", show_header=True, header_style="bold magenta")
            rel_table.add_column("Relationship", style="cyan")
            rel_table.add_column("Count", justify="right", style="green")
            
            for rel_type, count in status_data["neo4j"]["relationships"].items():
                rel_table.add_row(rel_type, str(count))
            
            console.print(rel_table)
        
    except Exception as e:
        console.print(f"❌ Error getting status: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def clear():
    """Clear all data from the Neo4j graph"""
    setup_logging()
    
    if not typer.confirm("⚠️  This will delete ALL data from the Neo4j graph. Are you sure?"):
        console.print("Operation cancelled.", style="yellow")
        return
    
    try:
        sync = KnowledgeGraphSync()
        sync.neo4j_manager.clear_graph()
        console.print("✅ Graph cleared successfully!", style="bold green")
    except Exception as e:
        console.print(f"❌ Error clearing graph: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def test_connection():
    """Test database connections"""
    setup_logging()
    console.print(Panel("Testing Database Connections", style="bold blue"))
    
    try:
        # Test PostgreSQL
        sync = KnowledgeGraphSync()
        customers = sync.pg_manager.get_customers()
        console.print(f"✅ PostgreSQL: Connected ({len(customers)} customers found)", style="bold green")
        
        # Test Neo4j
        stats = sync.neo4j_manager.get_graph_statistics()
        total_nodes = sum(stats[k] for k in stats if k != "relationships")
        console.print(f"✅ Neo4j: Connected ({total_nodes} nodes found)", style="bold green")
        
        console.print("\n🎉 All connections successful!", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Connection test failed: {e}", style="bold red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
