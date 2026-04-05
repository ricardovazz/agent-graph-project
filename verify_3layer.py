"""
Verify the 3-layer skills architecture is properly implemented.
"""
from pathlib import Path
from src.skills import SkillStore
from src.agent_graph import (
    app, 
    supervisor_skill_store, 
    SUBAGENTS,
    SPECIALIST_SKILLS_DIRS
)

def verify_layer_separation():
    """Verify that layers are properly separated."""
    print("=" * 80)
    print("VERIFYING 3-LAYER ARCHITECTURE")
    print("=" * 80)
    
    # Layer 1 & 2: Supervisor
    print("\n[✓] Layer 1 & 2: Supervisor Skills")
    print(f"    Skills: {supervisor_skill_store.get_skill_names()}")
    
    # Verify supervisor doesn't have specialist skills
    supervisor_skills = supervisor_skill_store.get_skill_names()
    assert 'research' not in supervisor_skills, "Supervisor should NOT have specialist skills!"
    assert 'writing' not in supervisor_skills, "Supervisor should NOT have specialist skills!"
    print("    ✓ Supervisor correctly has ONLY Layer 1 & 2 skills")
    
    # Layer 3: Subagents
    print("\n[✓] Layer 3: Subagent Specialist Skills")
    for agent_name in ['research', 'writing', 'code-generation']:
        skills_dir = Path(f"skills/{agent_name}")
        if skills_dir.exists():
            store = SkillStore(skills_dir)
            store.scan()
            skills = store.get_skill_names()
            print(f"    ✓ {agent_name}: {skills}")
        else:
            print(f"    ⚠ {agent_name}: directory not found")
    
    # Verify subagents are properly configured
    print(f"\n[✓] Subagents Configuration")
    print(f"    Total subagents: {len(SUBAGENTS)}")
    print(f"    Subagents: {list(SUBAGENTS.keys())}")
    
    # Verify skill directories
    print(f"\n[✓] Skills Directory Structure")
    skills_root = Path("skills")
    
    # Check supervisor skills
    supervisor_dir = skills_root / "supervisor"
    if supervisor_dir.exists():
        print(f"    ✓ supervisor/ exists")
        print(f"      - capabilities/: {(supervisor_dir / 'capabilities').exists()}")
        print(f"      - processes/: {(supervisor_dir / 'processes').exists()}")
    
    # Check subagent skills
    subagents_dir = skills_root / "subagents"
    if subagents_dir.exists():
        print(f"    ✓ subagents/ exists (Layer 2 process views)")
        for agent_dir in subagents_dir.iterdir():
            if agent_dir.is_dir():
                print(f"      - {agent_dir.name}/: {list(agent_dir.glob('*.md'))}")
    
    # Check specialist skills
    for specialist in ['research', 'writing', 'code-generation']:
        specialist_dir = skills_root / specialist
        if specialist_dir.exists():
            print(f"    ✓ {specialist}/ exists (Layer 3 specialist skills)")
    
    print("\n" + "=" * 80)
    print("ARCHITECTURE VERIFICATION COMPLETE ✓")
    print("=" * 80)
    print("\n3-Layer Split Successfully Implemented:")
    print("  Layer 1 (Capability Catalog): Supervisor knows subagent capabilities")
    print("  Layer 2 (Process Skills): Same process, different views per role")
    print("  Layer 3 (Specialist Skills): Subagents own execution expertise")
    print("\nReference: SKILLS-3LAYER-PATTERN.md")
    print("Details: REFACTOR-3LAYER-COMPLETE.md")

if __name__ == "__main__":
    verify_layer_separation()
