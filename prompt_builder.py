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

KEY: the variables in rtdl are ONLY used to pass in and out params of a skill or a sub-task,
in other word, they are the representation of data flowing as the task being executed. That means,
The assign operation can ONLY happen when do a skill or call a sub-task, and these statement is invalid:
state x: int;
x = x + 1;
state y: int;
y = x; 

An example of rtdl(assuming we have a skill Demo(inpar1, inpar2, outpar1, outpar2))
def task Example(t1: int, t2:int; t3: int, t4: int){
    Sequence{
        do Demo(inpar1=t1,inpar2=t2;outpar1->t3,outpar2->t4);
    }
}

If you have already know the exact value of t1, t2(for example, 1 and 2), then you don't need to 
write them as params of 'task Example'; instead, you can write like:
def task Example(;t3: int, t4: int){
    Sequence{
        do Demo(inpar1=1,inpar2=2;outpar1->t3,outpar->t4);
    }
}
Moreover, if a task doesn't need to pass out any params, which in 'task Example' means t3 and t4
are redundant, then you can write it like:
def task Example(;){
    state local_out1: int;
    state local_out2: int;
    Sequence{
        do Demo(inpar1=1,inpar2=2;outpar1->local_out1,outpar2->local_out2);
    }
}

Usually, if a task is the main task, then it doesn't need any in and out params.

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