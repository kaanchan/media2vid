#!/bin/bash

# 🤖 Claude Code Agent Launcher
# Quick-start script for parallel agent development

set -e

echo "🤖 Claude Code Agentic Workflow Initializer"
echo "=============================================="
echo ""

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is required but not installed."
    echo "   Install from: https://cli.github.com/"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository. Please run from project root."
    exit 1
fi

echo "✅ Environment checks passed"
echo ""

# Get open issues that could be automated
echo "📋 Checking for agent-ready issues..."
AGENT_READY_ISSUES=$(gh issue list --label "agent-ready" --state open --json number,title || echo "")

if [ -z "$AGENT_READY_ISSUES" ] || [ "$AGENT_READY_ISSUES" = "[]" ]; then
    echo "⚠️  No issues labeled 'agent-ready' found."
    echo ""
    echo "🏷️  Available issues that could be automated:"
    gh issue list --state open --json number,title,labels | jq -r '.[] | "  #\(.number): \(.title)"'
    echo ""
    echo "💡 To enable agent processing:"
    echo "   gh issue edit <issue_number> --add-label agent-ready"
    echo ""
    read -p "Would you like to add 'agent-ready' label to specific issues? (y/N): " add_labels
    
    if [[ $add_labels =~ ^[Yy]$ ]]; then
        echo ""
        echo "📋 Current open issues:"
        gh issue list --state open --json number,title | jq -r '.[] | "#\(.number): \(.title)"'
        echo ""
        read -p "Enter issue numbers to make agent-ready (comma-separated): " issue_numbers
        
        if [ -n "$issue_numbers" ]; then
            IFS=',' read -ra ISSUES <<< "$issue_numbers"
            for issue in "${ISSUES[@]}"; do
                issue=$(echo "$issue" | tr -d ' ')
                echo "🏷️  Adding agent-ready label to issue #$issue..."
                gh issue edit "$issue" --add-label agent-ready || echo "   ⚠️ Failed to label issue #$issue"
            done
            echo ""
            echo "✅ Labels added! Re-run this script to proceed with agent dispatch."
            exit 0
        fi
    fi
    
    echo ""
    echo "🚫 No agent-ready issues available. Exiting."
    exit 0
fi

echo "🤖 Found agent-ready issues!"
echo "$AGENT_READY_ISSUES" | jq -r '.[] | "  #\(.number): \(.title)"'
echo ""

# Ask user which approach they want
echo "🔀 Choose agent deployment method:"
echo "  1. Manual dispatch (trigger GitHub Actions workflow)"  
echo "  2. Local multi-session (create branches + start Claude Code sessions)"
echo "  3. Show agent commands only (for manual execution)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Triggering GitHub Actions workflow..."
        ISSUE_NUMS=$(echo "$AGENT_READY_ISSUES" | jq -r '.[].number' | tr '\n' ',' | sed 's/,$//')
        gh workflow run agent-dispatcher.yml -f issue_numbers="$ISSUE_NUMS" -f agent_type="auto"
        echo "✅ Workflow dispatched!"
        echo ""
        echo "📊 Monitor progress at:"
        echo "   https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/actions"
        ;;
        
    2)
        echo ""
        echo "🌿 Creating local agent branches and sessions..."
        
        # Create agent branches locally
        ISSUE_DATA=$(echo "$AGENT_READY_ISSUES" | jq -c '.[]')
        while IFS= read -r issue_line; do
            ISSUE_NUM=$(echo "$issue_line" | jq -r '.number')
            ISSUE_TITLE=$(echo "$issue_line" | jq -r '.title')
            
            # Determine agent type based on title
            if [[ "$ISSUE_TITLE" =~ (menu|input|prompt|cleanup) ]]; then
                AGENT_TYPE="menu-refactor"
            elif [[ "$ISSUE_TITLE" =~ (cache|performance|optimization) ]]; then
                AGENT_TYPE="cache-optimizer"  
            elif [[ "$ISSUE_TITLE" =~ (test|fix.*test|expectation) ]]; then
                AGENT_TYPE="test-fixer"
            else
                AGENT_TYPE="general"
            fi
            
            BRANCH_NAME="agent/${AGENT_TYPE}-issue-${ISSUE_NUM}"
            
            echo "🌿 Creating branch: $BRANCH_NAME"
            git checkout main
            git checkout -b "$BRANCH_NAME"
            
            # Create agent instructions
            mkdir -p .agents
            cat > ".agents/agent-${ISSUE_NUM}-instructions.md" << EOF
# Agent Instructions - Issue #${ISSUE_NUM}

**Agent Type:** ${AGENT_TYPE}
**Branch:** ${BRANCH_NAME}
**Issue:** https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/issues/${ISSUE_NUM}
**Title:** ${ISSUE_TITLE}

## Task
Process Issue #${ISSUE_NUM} according to ${AGENT_TYPE} specialization.

## Status: INITIALIZED
**Started:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Agent ID:** agent-${AGENT_TYPE}-${ISSUE_NUM}

## Progress Log
- [x] Branch created
- [ ] Analysis complete
- [ ] Implementation started
- [ ] Testing completed
- [ ] PR created
- [ ] Issue resolved
EOF
            
            git add .agents/
            git commit -m "🤖 Initialize ${AGENT_TYPE} agent for issue #${ISSUE_NUM}

Agent spawned for automated processing of issue #${ISSUE_NUM}.
Branch: ${BRANCH_NAME}

🤖 Generated with Claude Agent System"
            
            echo "📝 Agent instructions created in .agents/agent-${ISSUE_NUM}-instructions.md"
            
        done <<< "$ISSUE_DATA"
        
        # Return to main branch
        git checkout main
        
        echo ""
        echo "🚀 Ready to start Claude Code agent sessions!"
        echo ""
        echo "💻 Start each agent in a separate terminal:"
        
        while IFS= read -r issue_line; do
            ISSUE_NUM=$(echo "$issue_line" | jq -r '.number')
            ISSUE_TITLE=$(echo "$issue_line" | jq -r '.title')
            
            if [[ "$ISSUE_TITLE" =~ (menu|input|prompt|cleanup) ]]; then
                AGENT_TYPE="menu-refactor"
            elif [[ "$ISSUE_TITLE" =~ (cache|performance|optimization) ]]; then
                AGENT_TYPE="cache-optimizer"  
            elif [[ "$ISSUE_TITLE" =~ (test|fix.*test|expectation) ]]; then
                AGENT_TYPE="test-fixer"
            else
                AGENT_TYPE="general"
            fi
            
            echo "   claude-code --session agent-${AGENT_TYPE}-${ISSUE_NUM}    # Issue #${ISSUE_NUM}: ${ISSUE_TITLE}"
        done <<< "$ISSUE_DATA"
        ;;
        
    3)
        echo ""
        echo "💻 Agent session commands:"
        echo ""
        
        ISSUE_DATA=$(echo "$AGENT_READY_ISSUES" | jq -c '.[]')
        while IFS= read -r issue_line; do
            ISSUE_NUM=$(echo "$issue_line" | jq -r '.number')
            ISSUE_TITLE=$(echo "$issue_line" | jq -r '.title')
            
            if [[ "$ISSUE_TITLE" =~ (menu|input|prompt|cleanup) ]]; then
                AGENT_TYPE="menu-refactor"
            elif [[ "$ISSUE_TITLE" =~ (cache|performance|optimization) ]]; then
                AGENT_TYPE="cache-optimizer"  
            elif [[ "$ISSUE_TITLE" =~ (test|fix.*test|expectation) ]]; then
                AGENT_TYPE="test-fixer"
            else
                AGENT_TYPE="general"
            fi
            
            echo "# Terminal for Issue #${ISSUE_NUM} (${AGENT_TYPE}): ${ISSUE_TITLE}"
            echo "claude-code --session agent-${AGENT_TYPE}-${ISSUE_NUM}"
            echo ""
        done <<< "$ISSUE_DATA"
        
        echo "📖 Agent instructions will be available in .agents/ directory"
        ;;
        
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🎯 Agent system ready!"
echo ""
echo "📚 Documentation:"
echo "   - Agent coordination: .agents/agent-coordinator.md"
echo "   - Agent templates: .agents/templates/"
echo ""
echo "🤖 Happy automated development!"