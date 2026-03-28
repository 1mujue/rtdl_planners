import json


def build_prompts(user_task: str, world_state: dict, skills: list[dict]) -> tuple[str, str]:
    system_prompt = """
You are a robot task planner.

You must generate a valid json object.
The json object must contain exactly these keys:
- plan_summary
- assumptions
- rtdl

Rules:
- Only use skills listed in the provided skills document.
- Do not invent robots, objects, or relations that are not present in the world state.
- The value of "rtdl" must be a complete RTDL program as a string.

Example json format:
{
  "plan_summary": "short summary",
  "assumptions": ["assumption 1", "assumption 2"],
  "rtdl": "task Demo { ... }"
}

The syntactic of rtdl:
CompUnit -> { TaskDef }
TaskDef -> 'def' 'task' ID '(' TaskParams ')' TaskBody
TaskParams -> [InParamList] ';' [OutParamList] 
InParamList -> ParamDecl {',' ParamDecl}
OutParamList -> ParamDecl {',' ParamDecl}
ParamDecl -> ID ':' Type

TaskBody -> '{' {StateDecl} Node '}'
StateDecl -> 'state' ID ':' Type ';'

Node -> CompositeNode
| DecoratorNode
| LeafNode

CompositeNode -> SequenceNode
| SelectorNode
SequenceNode -> 'sequence' ChildBlock
SelectorNode -> 'selector' ChildBlock
ChildBlock -> '{' Node { Node } '}'

DecoratorNode -> RetryNode
| TimeoutNode
RetryNode -> 'retry' '(' INT ')' Node
TimeoutNode -> 'timeout' '(' Duration ')' Node

LeafNode -> SkillCall
| TaskCall
| CheckStmt
| WaitStmt

SkillCall -> 'do' ID '(' BindSections ')' ';'
TaskCall -> 'call' ID '(' BindSections ')' ';'
BindSections -> [InBindings] ';' [OutBindings]
InBindings -> InBinding {',' InBinding}
OutBindings -> OutBinding {',' OutBinding}
InBinding -> ID '=' Value
OutBinding -> ID '->' Ref

Value -> Literal 
| Ref
Ref -> ID

CheckStmt -> 'check' '(' CondExp ')' ';'
CondExp -> LOrExp
LOrExp -> LAndExp {'||' LAndExp}
LAndExp -> EqExp {'&&' EqExp }
EqExp -> RelExp { ('==' | '!=') RelExp }
RelExp -> AddExp [ ('>=' | '>' | '<' | '<=') AddExp ]
AddExp -> MulExp { ('+' | '-') MulExp }
MulExp -> UnaryExp { ('*' | '/' | '%') UnaryExp}
UnaryExp -> ('-' | '!') UnaryExp | PrimaryExp
PrimaryExp -> Literal
| Ref
| '(' CondExp ')'

WaitStmt -> 'wait' '(' Duration ')' ';'

Literal -> INT
| FLOAT
| STRING
| BOOL
Duration -> INT

Type -> BuiltinType 
BuiltinType -> 'bool'
| 'int'
| 'float'
| 'string'

Note that the assign operation is ONLY ALLOWED in rtdl when assign the output
of a skill to a variable. That means, you can't write something like:
state x: float;
x = 1.0;
""".strip()

    user_prompt = f"""
Available skills:
{json.dumps(skills, ensure_ascii=False, indent=2)}

Current world state:
{json.dumps(world_state, ensure_ascii=False, indent=2)}

User task:
{user_task}
""".strip()

    return system_prompt, user_prompt