def update_layout_wrapper(fig):
    return (fig.update_layout(
        titlefont={'family': 'Optima, Bold', 'size': 26, 'color': 'black'},
        font={'family': 'Optima', 'size': 16},
        xaxis={
               'showgrid': False,
               'showline': True,
               'linecolor': 'black'
               },
        yaxis={
               'showgrid': True,
               'gridcolor': '#F6F6F6',
               'showline': True,
               'linecolor': 'black'
               },
        paper_bgcolor='white',
        plot_bgcolor='white',
        legend={
            'bgcolor': 'white',
            'xanchor': 'center',
            'yanchor': 'top',
            'x': .5,
            'y': -.2,
            'orientation': 'h',
            'title': {'font': {'family': 'Optima', 'size': 18}},
            'tracegroupgap': 20
        },
        annotations=[{
            'text': "Source: Anicca Research. Seeded with data from Coin Metrics and Hashrate Index.",
            'font': {
                'size': 18,
                'color': 'black',
            },
            'showarrow': False,
            'align': 'left',
            'valign': 'top',
            # 'y': 0.25,
            'x': 0,
            'y': 1.06,
            'xref': 'paper',
            'yref': 'paper',
        }]
    ))
