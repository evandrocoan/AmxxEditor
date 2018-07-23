// SYNTAX TEST "Packages/AmxxEditor/AmxxEditorPawn.sublime-syntax"


stock CC_ShowActivity(id)
{
    switch(CC_ACTIVITY_POINTER)
    {
        case 1: CC_SendMessage(0, "%L: %s", LANG_PLAYER, szPrefix, szMessage)
        //    ^ keyword.control.pawn - storage.type.vars.pawn
    }
}
