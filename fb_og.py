# -*- coding: utf-8 -*-

@app.route('/og_repeater', methods=['get'])
def open_graph_repeater():
    return render_template('og.html', tags=request.args, url=request.url)

@app.route('/og_quote', methods=['get'])
def og_quote():

    echoId = request.args.get('ref')

    try:
        echo = Echo.query.filter_by(id = echoId).first()
        if not echo:
            raise ServerException(ErrorMessages.ECHO_NOT_FOUND, \
                ServerException.ER_BAD_ECHO)
        quote = echo.quote
        if not quote or quote.deleted:
            raise ServerException(ErrorMessages.QUOTE_NOT_FOUND, \
                ServerException.ER_BAD_QUOTE)

        # TODO there is some code duplication with get_quotes below... we should think if it could be avoided
        is_echo = echo.user_id != quote.reporter_id
        if is_echo:
            quote.created = echo.created
            quote.reporter = echo.user

        tags = {
            'og:type': 'echoios:quote',
            'og:title': '"%s"' % quote.content,
            'og:image': 'http://graph.facebook.com/%s/picture?width=200' % quote.source.fbid,
            'og:description': u'\u2014 %s %s' % (quote.source.first_name, quote.source.last_name)
        }
        return render_template('og.html', tags=tags, url=request.url) 
    except ServerException as e:
        return format_response(None, e)