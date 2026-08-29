import com.sap.it.script.v2.api.Message

def Message processData(Message message) {
    def body = message.getBody(java.lang.String) ?: ""

    def extracted = (body =~ /(?i)hello world!?/)
    def value = extracted.find() ? extracted.group() : ""

    message.setProperty("extractedText", value)
    message.setBody(value)

    return message
}