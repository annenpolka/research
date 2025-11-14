---
name: skill-creator
description: Creating custom Claude Code skills. Use when the user wants to create a new skill, needs help structuring a skill, or wants to understand how skills work. Also use when the user asks about skill best practices or troubleshooting.
allowed-tools: Read, Write, Grep, Glob, Bash, TodoWrite
---

# Skill Creator - Meta Skill for Claude Code

This skill helps you create new custom skills for Claude Code. It guides you through the entire workflow from understanding user requirements to implementing and testing a functional skill.

## When to Use This Skill

Activate this skill when the user:
- Explicitly asks to create a new skill
- Wants to automate a repetitive workflow
- Needs a specialized capability for their project
- Asks about skill structure or best practices
- Wants to convert an existing workflow into a skill

## Skill Creation Workflow

Create a todo list with all the steps below and work through them systematically.

### 1. Understand Requirements

Ask the user clarifying questions to understand:
- **Purpose**: What problem does this skill solve?
- **Scope**: What tools and operations are needed?
- **Context**: When should Claude automatically invoke this skill?
- **Location**: Personal skill (~/.claude/skills/) or project skill (.claude/skills/)?

Key questions to ask:
- "What tasks should this skill automate?"
- "When should Claude use this skill automatically?"
- "Does this skill need to modify files, or is it read-only?"
- "Should this skill be shared with your team or kept personal?"

### 2. Design the Skill Structure

Based on requirements, determine:

**Skill Complexity:**
- **Simple**: Single SKILL.md file (< 500 lines, straightforward logic)
- **Moderate**: SKILL.md + supporting files (examples, templates)
- **Complex**: Multi-file structure with scripts and documentation

**Tool Permissions:**
- **Read-only**: `allowed-tools: Read, Grep, Glob`
- **Code modification**: Add `Edit, Write`
- **System operations**: Add `Bash`
- **Full access**: Omit `allowed-tools` field

**File Structure Template:**
```
skill-name/
├── SKILL.md           # Main skill definition (required)
├── REFERENCE.md       # Additional reference material (optional)
├── EXAMPLES.md        # Usage examples (optional)
├── templates/         # File templates (optional)
└── scripts/           # Helper scripts (optional)
```

### 3. Create SKILL.md

Generate the SKILL.md file with proper structure:

#### Required Frontmatter

```yaml
---
name: skill-name-here
description: Clear description of what the skill does and when to use it (max 1024 chars)
allowed-tools: Read, Write, Edit, Grep, Glob, Bash  # Optional, customize based on needs
---
```

**Naming Rules:**
- Lowercase letters, numbers, hyphens only
- Max 64 characters
- Descriptive and unique
- Examples: `api-tester`, `commit-msg-helper`, `code-reviewer`

**Description Best Practices:**
- Start with action verbs
- Specify WHEN to use the skill
- Mention key capabilities
- Keep it concise but comprehensive
- Example: "Creating API integration tests with mocking. Use when the user needs to test REST APIs, create mock responses, or validate API contracts."

#### Content Structure

```markdown
# [Skill Name]

[1-2 sentence overview of the skill's purpose]

## When to Use This Skill

[Specific scenarios that trigger this skill]

## Workflow

Make a todo list for all the tasks in this workflow and work on them one after another

### 1. [First Step]

[Detailed instructions for the first step]
[Include code examples, commands, or file patterns]

### 2. [Second Step]

[Continue with clear, actionable steps]

### 3. [Additional Steps...]

[As many steps as needed]

## Best Practices

- [Key principle 1]
- [Key principle 2]
- [Important considerations]

## Troubleshooting

**Problem**: [Common issue]
**Solution**: [How to fix it]

## Examples

### Example 1: [Use Case]

[Show concrete example with code]

### Example 2: [Another Use Case]

[Another concrete example]

## Wrap Up

[Final message to display to user when skill completes]
[Summary of what was created]
[Next steps or usage instructions]
```

### 4. Add Supporting Files (if needed)

For complex skills, create additional documentation:

**REFERENCE.md**: Technical details, API docs, configuration options
**EXAMPLES.md**: Extended examples and use cases
**templates/**: Starter files and boilerplates
**scripts/**: Utility scripts the skill references

Example reference file:
```markdown
# [Skill Name] Reference

## Configuration Options

[Document all configurable aspects]

## Technical Details

[Deep-dive information]

## Advanced Usage

[Power-user features]
```

### 5. Validate the Skill

Before finalizing, check:

- [ ] YAML frontmatter is valid (use a YAML validator)
- [ ] Name follows naming rules (lowercase, hyphens, max 64 chars)
- [ ] Description is clear and comprehensive (< 1024 chars)
- [ ] `allowed-tools` matches required permissions
- [ ] Workflow steps are numbered and actionable
- [ ] Examples are concrete and realistic
- [ ] Markdown formatting is correct
- [ ] All file references are accurate

**Validation Commands:**
```bash
# Check if skill directory exists
ls -la ~/.claude/skills/skill-name/  # or .claude/skills/skill-name/

# Validate SKILL.md exists
cat ~/.claude/skills/skill-name/SKILL.md | head -20

# Test YAML frontmatter
head -10 ~/.claude/skills/skill-name/SKILL.md
```

### 6. Test the Skill

Create a test scenario:

1. **Trigger Test**: Describe a scenario that should activate the skill
2. **Execution Test**: Verify the skill follows its workflow correctly
3. **Output Test**: Confirm the skill produces expected results

Example test plan:
```markdown
## Test Scenario 1: [Description]
User message: "Can you [trigger phrase]?"
Expected: Skill activates and follows steps 1-5
Result: [Pass/Fail]

## Test Scenario 2: [Description]
User message: "[Another trigger]"
Expected: [Specific outcome]
Result: [Pass/Fail]
```

### 7. Document Usage

Provide the user with:

1. **Activation Instructions**: How to trigger the skill
2. **Location**: Where the skill was installed
3. **Next Steps**: How to use or modify the skill
4. **Sharing**: How to share with team (if project skill)

Example completion message:
```
✅ Skill Created: skill-name

Location: .claude/skills/skill-name/

Activation:
The skill will automatically activate when you ask Claude to [describe trigger scenarios].

Files Created:
- SKILL.md (main skill definition)
- EXAMPLES.md (usage examples)
- templates/starter.txt (template file)

Testing:
Try saying: "[example trigger phrase]"

Sharing:
This is a project skill. Commit the .claude/skills/ directory to share with your team:
  git add .claude/skills/skill-name/
  git commit -m "Add skill-name skill"
  git push
```

## Skill Design Patterns

### Pattern 1: Workflow Automation
Use for multi-step processes (builds, deployments, testing)
- Clear numbered steps
- TodoWrite integration
- Validation at each stage
- Final summary

### Pattern 2: Code Generation
Use for generating files or code snippets
- Template-based approach
- User input collection
- Validation of generated code
- Examples of usage

### Pattern 3: Analysis & Review
Use for code review, auditing, or analysis tasks
- Read-only tools (`allowed-tools: Read, Grep, Glob`)
- Structured output format
- Clear criteria/checklist
- Actionable recommendations

### Pattern 4: Interactive Guide
Use for teaching or guiding through complex tasks
- Progressive disclosure
- Step-by-step instructions
- Decision trees
- FAQs and troubleshooting

## Best Practices

### Do's
- ✅ Keep descriptions action-oriented and specific
- ✅ Use TodoWrite for multi-step workflows
- ✅ Provide concrete examples
- ✅ Validate YAML frontmatter syntax
- ✅ Test the skill before delivering
- ✅ Document edge cases and troubleshooting
- ✅ Use `allowed-tools` for security-sensitive operations
- ✅ Keep SKILL.md focused (< 500 lines), use supporting files for details

### Don'ts
- ❌ Don't use uppercase or special characters in skill names
- ❌ Don't make descriptions vague or generic
- ❌ Don't create overly complex single-file skills
- ❌ Don't forget to test trigger scenarios
- ❌ Don't grant excessive tool permissions
- ❌ Don't skip validation steps
- ❌ Don't forget to explain when skill should activate

## Troubleshooting

### Problem: Claude doesn't activate the skill

**Possible Causes:**
- Description doesn't match user's language/intent
- Skill name conflicts with existing skill
- YAML frontmatter has syntax errors

**Solutions:**
- Review and improve description to cover trigger scenarios
- Check for duplicate skill names
- Validate YAML syntax

### Problem: Skill has wrong permissions

**Solution:**
- Add or modify `allowed-tools` in frontmatter
- Common sets:
  - Read-only: `Read, Grep, Glob`
  - Code editing: `Read, Write, Edit, Grep, Glob`
  - Full dev workflow: `Read, Write, Edit, Grep, Glob, Bash, TodoWrite`

### Problem: Skill is too complex

**Solution:**
- Split into multiple simpler skills
- Move detailed content to supporting files (REFERENCE.md, EXAMPLES.md)
- Use progressive disclosure
- Create modular workflows

## Wrap Up

After creating the skill, provide the user with:

1. **Summary**: What was created and where
2. **Files**: List all files generated
3. **Testing**: How to test the skill
4. **Usage**: Example trigger phrases
5. **Sharing**: Instructions for team distribution (if applicable)

Example:
```
🎉 Successfully created the [skill-name] skill!

📁 Location: .claude/skills/skill-name/

📄 Files:
- SKILL.md (main definition)
- EXAMPLES.md (usage examples)

🧪 Test it:
Try: "[example trigger phrase]"

📚 Next Steps:
- Test the skill with different scenarios
- Customize the workflow if needed
- Share with your team by committing to git

The skill is now active and Claude will automatically use it when appropriate.
```
