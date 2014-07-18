ace.define(
"ace/mode/oz_highlight_rules",
["require","exports","module","ace/lib/oop","ace/mode/text_highlight_rules"],
function(e,t,n)
{
    "use strict";
    var r=e("../lib/oop"),i=e("./text_highlight_rules").TextHighlightRules,s=function()
    {
        /*ok*/
        var e="andthen|at|attr|case|catch|choice|class|cond|declare|define|dis|do|div|else|elsecase|elseif|elseof|end|export|fail|feat|finally|from|for|fun|functor|if|import|in|local|lock|meth|mod|not|of|or|orelse|prepare|proc|prop|raise|require|self|skip|suchthat|then|thread|try",
        t="true|false|nil|unit",
        /*nok*/
        n="",
        r="",
        i="",
        s="",
        o=this.createKeywordMapper(
        {
            keyword:e,
            "support.function":n,
            "invalid.deprecated":s,
            "constant.library":r,
            "constant.language":t,
            "invalid.illegal":i,
            "variable.language":"self"
        },
        "identifier"),
        u="(?:(?:[1-9]\\d*)|(?:0))",
        a="(?:0[xX][\\dA-Fa-f]+)",
        f="(?:"+u+"|"+a+")",
        l="(?:\\.\\d+)",
        c="(?:\\d+)",
        h="(?:(?:"+c+"?"+l+")|(?:"+c+"\\.))",
        p="(?:"+h+")";
        /*ok*/
        this.$rules={
            start:[
                {stateName:"bracketedComment", //ok
                onMatch:function(e,t,n)
                {
                    return n.unshift(this.next,e.length,t),"comment"
                },
                regex:/\/\*/,
                next:[{
                    onMatch:function(e,t,n)
                    {
                        return e.length==n[1]?(n.shift(),n.shift(),this.next=n.shift()):this.next="","comment"
                    },
                    regex:/\*\//,
                    next:"start"},
                {defaultToken:"comment"}]},
            {token:"comment",regex:"\\%.*$"},
            {token:"punctuation.definition.string.begin", //ok
                regex:'"',
                push:[
                {token:"constant.character.escape",
                    regex:"\\\\."},
                {token:"punctuation.definition.string.end",
                    regex:'"',
                    next:"pop"},
                {defaultToken:"string.quoted.double.oz"}]},
            {token:"punctuation.definition.string.begin", //ok
                regex:"'",
                push:[
                {token:"constant.character.escape.apostrophe",
                    regex:"\\\\."},
                {token:"punctuation.definition.string.end",
                    regex:"'",
                    next:"pop"},
                {defaultToken:"string.quoted.single"}]},
            {token:"constant.numeric",
                regex:p},
            {token:"constant.numeric",
                regex:f+"\\b"},
            {token:o,
                regex:"[a-zA-Z_$][a-zA-Z0-9_$]*\\b"},
            {token:"keyword.operator",
                regex:"\\+|\\-|\\*|\\/|\\#|\\^|~|<|>|<=|=>|==|\\\=|\\!|\\_|\\:|\\.\\.\\.|\\.|\\:\\=|\\\\\=\\:|<\\:|\\=<\\:|>\\:|>\\=\\:|;|@"},
            {token:"paren.lparen",
                regex:"[\\[\\(\\{]"},
            {token:"paren.rparen",
                regex:"[\\]\\)\\}]"},
            {token:"text",regex:"\\s+|\\w+"}]
        },
        this.normalizeRules()
    };
    r.inherits(s,i),t.OzHighlightRules=s
}),

ace.define(
"ace/mode/folding/oz",
["require","exports","module","ace/lib/oop","ace/mode/folding/fold_mode","ace/range","ace/token_iterator"],
function(e,t,n)
{
    "use strict";
    var r=e("../../lib/oop"),i=e("./fold_mode").FoldMode,s=e("../../range").Range,o=e("../../token_iterator").TokenIterator,u=t.FoldMode=function(){};
    r.inherits(u,i),
    function()
    {
        this.foldingStartMarker=/\b(fun|proc|then|do|local)\b|{\s*$|(\[=*\[)|(\/\*)/,
        this.foldingStopMarker=/\bend\b|^\s*}|\]=*\]|(\*\/)/,
        
        this.getFoldWidget=function(e,t,n)
        {
            var r=e.getLine(n),
            i=this.foldingStartMarker.test(r),
            s=this.foldingStopMarker.test(r);
            if(i&&!s)
            {
                var o=r.match(this.foldingStartMarker);
                if(o[1]=="then"&&/\belseif\b/.test(r))return; //if(o[1]=="local"&&/\bin\b/.test(r))return;
                if(o[1])
                {
                    if(e.getTokenAt(n,o.index+1).type==="keyword") return"start"
                }
                else
                {
                    if(!o[2] && !o[3])return"start";
                    var u=e.bgTokenizer.getState(n)||"";
                    if(u[0]=="bracketedComment"||u[0]=="bracketedString")return"start"
                }
            }
            if(t!="markbeginend"||!s||i&&s)return"";
            var o=r.match(this.foldingStopMarker);
            if(o[0]==="end")
            {
                if(e.getTokenAt(n,o.index+1).type==="keyword")return"end"
            }
            else
            {
                if(o[0][0]!=="]")return"end";
                var u=e.bgTokenizer.getState(n-1)||"";
                if(u[0]=="bracketedComment"||u[0]=="bracketedString")return"end"
            }
        },
        this.getFoldWidgetRange=function(e,t,n)
        {
            var r=e.doc.getLine(n),
            i=this.foldingStartMarker.exec(r);
            if(i)return i[1]?this.ozBlock(e,n,i.index+1):i[3]?e.getCommentFoldRange(n,i.index+1):this.openingBracketBlock(e,"{",n,i.index);
            var i=this.foldingStopMarker.exec(r);
            if(i)return i[0]==="end"&&e.getTokenAt(n,i.index+1).type==="keyword"?this.ozBlock(e,n,i.index+1):i[0][0]==="/"?e.getCommentFoldRange(n,i.index+1):this.closingBracketBlock(e,"}",n,i.index+i[0].length)
        },
        this.ozBlock=function(e,t,n)
        {
            // i : if wanna close upper block (-1), lower block(1)
            var r=new o(e,t,n),i={"fun":1,local:1,"do":1,"proc":1,then:1,elseif:-1,end:-1,until:-1},u=r.getCurrentToken();
            if(!u||u.type!="keyword")return;
            var a=u.value,f=[a],l=i[a];
            if(!l)return;
            var c=l===-1?r.getCurrentTokenColumn():e.getLine(t).length,h=t;r.step=l===-1?r.stepBackward:r.stepForward;
            while(u=r.step())
            {
                if(u.type!=="keyword")continue;
                var p=l*i[u.value];
                if(p>0)f.unshift(u.value);
                else if(p<=0)
                {
                    f.shift();
                    if(!f.length&&u.value!="elseif")break;
                    if(!f.length&&u.value!="in")break;
                    p===0&&f.unshift(u.value)
                }
            }
            var t=r.getCurrentTokenRow();
            return l===-1?new s(t,e.getLine(t).length,h,c):new s(h,c,t,r.getCurrentTokenColumn())
        }
    }.call(u.prototype)
}),


ace.define("ace/mode/oz",
["require","exports","module","ace/lib/oop","ace/mode/text","ace/mode/oz_highlight_rules","ace/mode/folding/oz","ace/range","ace/worker/worker_client"],
function(e,t,n)
{
    "use strict";
    var r=e("../lib/oop"),i=e("./text").Mode,s=e("./oz_highlight_rules").OzHighlightRules,o=e("./folding/oz").FoldMode,u=e("../range").Range,a=e("../worker/worker_client").WorkerClient,
    f=function()
    {
        this.HighlightRules=s,
        this.foldingRules=new o
    };
    
    r.inherits(f,i),
    
    function()
    {
        function n(t)
        {
            var n=0;
            for(var r=0;r<t.length;r++)
            {
                var i=t[r];i.type=="keyword"?i.value in e&&(n+=e[i.value]):i.type=="paren.lparen"?n++:i.type=="paren.rparen"&&n--
            }
            return n<0?-1:n>0?1:0
        }
        
        this.lineCommentStart="%",
        this.blockComment={start:"/*",end:"*/"};
        
        // e : Indent made when enter pressed after these keywords
        // t : Keywords which need to be indent back
        var e={"fun":1,then:1,"do":1,local:1,"proc":1,"else":1,elseif:1,end:-1,until:-1,"in":1},t=["else","elseif","end","until","in"];
        
        this.getNextLineIndent=function(e,t,r)
        {
            var i=this.$getIndent(t),s=0,o=this.getTokenizer().getLineTokens(t,e),u=o.tokens;
            return e=="start"&&(s=n(u)),s>0?i+r:s<0&&i.substr(i.length-r.length)==r&&!this.checkOutdent(e,t,"\n")?i.substr(0,i.length-r.length):i
        },
        
        this.checkOutdent=function(e,n,r)
        {
            if(r!="\n"&&r!="\r"&&r!="\r\n")return!1;
            if(n.match(/^\s*[\)\}\]]$/))return!0;
            var i=this.getTokenizer().getLineTokens(n.trim(),e).tokens;
            return!i||!i.length?!1:i[0].type=="keyword"&&t.indexOf(i[0].value)!=-1
        },
        
        this.autoOutdent=function(e,t,r)
        {
            var i=t.getLine(r-1),s=this.$getIndent(i).length,o=this.getTokenizer().getLineTokens(i,"start").tokens,a=t.getTabString().length,f=s+a*n(o),l=this.$getIndent(t.getLine(r)).length;if(l<f)return;t.outdentRows(new u(r,0,r+2,0))
        },
        
        this.createWorker=function(e)
        {
            var t=new a(["ace"],"ace/mode/oz_worker","Worker");
            return t.attachToDocument(e.getDocument()),t.on("error",function(t)
            {
                e.setAnnotations([t.data])
            }),
            t.on("ok",function(t)
            {
                e.clearAnnotations()
            }),t
        },
        
        this.$id="ace/mode/oz"
    }.call(f.prototype),t.Mode=f
})
