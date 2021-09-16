var max_conditions = 10;
var num_conditions = 1;
var target_vals = ["wordtrans", "word", "trans", "ex", "rhyme"];
var target_inners = ["見+訳", "見出し語", "訳語", "用例", "韻律"];
var option_vals = ["is", "starts", "includes", "ends", "regex"];
var option_inners = ["に一致する", "で始まる", "を含む", "で終わる", "の正規表現にハマる"];

function _addCondition(){
    var search = document.getElementById("searchForm");
    var div = document.createElement("div");
    div.setAttribute("class", "px-2 py-2")
    console.log(num_conditions);
    var target_select = document.createElement("select");
    target_select.name = "target_" + num_conditions;
    for (var i = 0; i < target_vals.length; i++) {
        var option = document.createElement("option");
        option.value = target_vals[i];
        option.innerHTML = target_inners[i];
        target_select.appendChild(option);
    }
    div.appendChild(target_select);
    div.innerHTML += "が";

    var keyword_text = document.createElement("input");
    keyword_text.type = "text";
    keyword_text.name = "keyword_" + num_conditions;
    keyword_text.value = "";
    div.appendChild(keyword_text);

    var option_select = document.createElement("select")
    option_select.name = "option_" + num_conditions;
    for (var i = 0; i < option_vals.length; i++) {
        var option = document.createElement("option");
        option.value = option_vals[i]
        option.innerHTML = option_inners[i]
        option_select.appendChild(option);
    }
    div.appendChild(option_select);

    search.appendChild(div);
    num_conditions++;

}
function addCondition(){
    if (num_conditions < max_conditions) {
        _addCondition();
    }
}

