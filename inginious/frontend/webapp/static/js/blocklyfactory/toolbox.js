var Toolbox = function() {

};

Toolbox.LOGIC_CATEGORY =
    '<category id="catLogic" colour="210" name="Logic">' +
    '   <block type="controls_if"></block>' +
    '   <block type="logic_compare"></block>' +
    '   <block type="logic_operation"></block>' +
    '   <block type="logic_negate"></block>' +
    '   <block type="logic_boolean"></block>' +
    '   <block type="logic_null"></block>' +
    '   <block type="logic_ternary"></block>' +
    '</category>';

Toolbox.LOOP_CATEGORY =
    '<category id="catLoops" colour="120" name="Loops">' +
    '   <block type="controls_repeat_ext">' +
    '       <value name="TIMES">' +
    '           <shadow type="math_number">' +
    '               <field name="NUM">10</field>' +
    '           </shadow>' +
    '       </value>' +
    '   </block>' +
    '   <block type="controls_whileUntil"></block>' +
    '   <block type="controls_for">' +
    '       <value name="FROM">' +
    '           <shadow type="math_number">' +
    '               <field name="NUM">1</field>' +
    '           </shadow>' +
    '       </value>' +
    '       <value name="TO">' +
    '           <shadow type="math_number">' +
    '               <field name="NUM">10</field>' +
    '           </shadow>' +
    '       </value>' +
    '       <value name="BY">' +
    '           <shadow type="math_number">' +
    '               <field name="NUM">1</field>' +
    '           </shadow>' +
    '       </value>' +
    '   </block>' +
    '   <block type="controls_forEach"></block>' +
    '   <block type="controls_flow_statements"></block>' +
    '</category>';

Toolbox.MATH_CATEGORY =
    '<category id="catMath" colour="230" name="Math">' +
    '  <block type="math_number"></block>' +
    '  <block type="math_arithmetic">' +
    '    <value name="A">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">1</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="B">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">1</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_single">' +
    '    <value name="NUM">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">9</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_trig">' +
    '    <value name="NUM">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">45</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_constant"></block>' +
    '  <block type="math_number_property">' +
    '    <value name="NUMBER_TO_CHECK">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">0</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_change">' +
    '    <value name="DELTA">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">1</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_round">' +
    '    <value name="NUM">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">3.1</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_on_list"></block>' +
    '  <block type="math_modulo">' +
    '    <value name="DIVIDEND">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">64</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="DIVISOR">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">10</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_constrain">' +
    '    <value name="VALUE">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">50</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="LOW">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">1</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="HIGH">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">100</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_random_int">' +
    '    <value name="FROM">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">1</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="TO">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">100</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="math_random_float"></block>' +
    '</category>';

Toolbox.TEXT_CATEGORY =
    '<category id="catText" colour="160" name="Text">' +
    '  <block type="text"></block>' +
    '  <block type="text_join"></block>' +
    '  <block type="text_append">' +
    '    <value name="TEXT">' +
    '      <shadow type="text"></shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_length">' +
    '    <value name="VALUE">' +
    '      <shadow type="text">' +
    '        <field name="TEXT">abc</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_isEmpty">' +
    '    <value name="VALUE">' +
    '      <shadow type="text">' +
    '        <field name="TEXT"></field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_indexOf">' +
    '    <value name="VALUE">' +
    '      <block type="variables_get">' +
    '        <field name="VAR">text</field>' +
    '      </block>' +
    '    </value>' +
    '    <value name="FIND">' +
    '      <shadow type="text">' +
    '        <field name="TEXT">abc</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_charAt">' +
    '    <value name="VALUE">' +
    '      <block type="variables_get">' +
    '        <field name="VAR">text</field>' +
    '      </block>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_getSubstring">' +
    '    <value name="STRING">' +
    '      <block type="variables_get">' +
    '        <field name="VAR">text</field>' +
    '      </block>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_changeCase">' +
    '    <value name="TEXT">' +
    '      <shadow type="text">' +
    '        <field name="TEXT">abc</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_trim">' +
    '    <value name="TEXT">' +
    '      <shadow type="text">' +
    '        <field name="TEXT">abc</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_print">' +
    '    <value name="TEXT">' +
    '      <shadow type="text">' +
    '        <field name="TEXT">abc</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="text_prompt_ext">' +
    '    <value name="TEXT">' +
    '      <shadow type="text">' +
    '        <field name="TEXT">abc</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '</category>';

Toolbox.LIST_CATEGORY =
    '<category id="catLists" colour="260" name="Lists">' +
    '  <block type="lists_create_with">' +
    '    <mutation items="0"></mutation>' +
    '  </block>' +
    '  <block type="lists_create_with"></block>' +
    '  <block type="lists_repeat">' +
    '    <value name="NUM">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">5</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="lists_length"></block>' +
    '  <block type="lists_isEmpty"></block>' +
    '  <block type="lists_indexOf">' +
    '    <value name="VALUE">' +
    '      <block type="variables_get">' +
    '        <field name="VAR">list</field>' +
    '      </block>' +
    '    </value>' +
    '  </block>' +
    '  <block type="lists_getIndex">' +
    '    <value name="VALUE">' +
    '      <block type="variables_get">' +
    '        <field name="VAR">list</field>' +
    '      </block>' +
    '    </value>' +
    '  </block>' +
    '  <block type="lists_setIndex">' +
    '    <value name="LIST">' +
    '      <block type="variables_get">' +
    '        <field name="VAR">list</field>' +
    '      </block>' +
    '    </value>' +
    '  </block>' +
    '  <block type="lists_getSublist">' +
    '    <value name="LIST">' +
    '      <block type="variables_get">' +
    '        <field name="VAR">list</field>' +
    '      </block>' +
    '    </value>' +
    '  </block>' +
    '  <block type="lists_split">' +
    '    <value name="DELIM">' +
    '      <shadow type="text">' +
    '        <field name="TEXT">,</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="lists_sort"></block>' +
    '</category>';

Toolbox.COLOUR_CATEGORY =
    '<category id="catColour" colour="20" name="Color">' +
    '  <block type="colour_picker"></block>' +
    '  <block type="colour_random"></block>' +
    '  <block type="colour_rgb">' +
    '    <value name="RED">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">100</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="GREEN">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">50</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="BLUE">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">0</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '  <block type="colour_blend">' +
    '    <value name="COLOUR1">' +
    '      <shadow type="colour_picker">' +
    '        <field name="COLOUR">#ff0000</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="COLOUR2">' +
    '      <shadow type="colour_picker">' +
    '        <field name="COLOUR">#3333ff</field>' +
    '      </shadow>' +
    '    </value>' +
    '    <value name="RATIO">' +
    '      <shadow type="math_number">' +
    '        <field name="NUM">0.5</field>' +
    '      </shadow>' +
    '    </value>' +
    '  </block>' +
    '</category>';

Toolbox.SEPARATOR = '<sep></sep>';

Toolbox.VARIABLES_CATEGORY = '<category id="catVariables" colour="330" custom="VARIABLE" name="Variables"></category>';

Toolbox.FUNCTIONS_CATEGORY = '<category id="catFunctions" colour="290" custom="PROCEDURE" name="Functions"></category>';

Toolbox.FULL =
    '<xml id="toolbox" style="display: none">'+
    Toolbox.LOGIC_CATEGORY +
    Toolbox.LOOP_CATEGORY +
    Toolbox.MATH_CATEGORY +
    Toolbox.TEXT_CATEGORY +
    Toolbox.LIST_CATEGORY +
    Toolbox.COLOUR_CATEGORY +
    Toolbox.SEPARATOR +
    Toolbox.VARIABLES_CATEGORY +
    Toolbox.FUNCTIONS_CATEGORY +
    '</xml>';
