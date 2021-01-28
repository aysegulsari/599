function initializeDataTable() {
    isDatatableFilled = true;
    $('#datatable').DataTable({
        destroy: true,
        searchPanes: {
            threshold: 1,
            columns: [1, 3, 4, 5, 6, 7, 8, 9]
        },
        columnDefs: [
            {
                targets: 6,
                render: function (data, type, row) {
                    if (type === 'sp') {
                        return data.split(' , ')
                    }
                    return data;
                },
                searchPanes: {
                    orthogonal: 'sp'
                }
            }, {
                targets: 7,
                render: function (data, type, row) {
                    if (type === 'sp') {
                        return data.split(' , ')
                    }
                    return data;
                },
                searchPanes: {
                    orthogonal: 'sp'
                }
            }, {
                targets: 8,
                render: function (data, type, row) {
                    if (type === 'sp') {
                        return data.split(' , ')
                    }
                    return data;
                },
                searchPanes: {
                    orthogonal: 'sp'
                }
            }
        ],
        responsive: true,
        dom: '<"dtsp-verticalContainer"<"dtsp-verticalPanes"P>l<"dtsp-dataTable"frtip>>',
        "processing": true,
        data: tweets['data']
    });
}

function drawTotalSentimentChart(pie_object) {
    let positiveCount = pie_object['positive'];
    let negativeCount = pie_object['negative'];
    let neutralCount = pie_object['neutral'];

    var myPieConfig = {
        type: "pie",
        plot: {
            borderColor: "#2B313B",
            borderWidth: 5,
            // slice: 90,
            valueBox: {
                placement: 'out',
                text: '%t\n%npv%',
                fontFamily: "Open Sans"
            },
            tooltip: {
                fontSize: '18',
                fontFamily: "Open Sans",
                padding: "5 10",
                text: "%npv%"
            },
            animation: {
                effect: 2,
                method: 5,
                speed: 900,
                sequence: 1,
                delay: 3000
            }
        },
        title: {
            fontColor: "#8e99a9",
            text: 'Sentiment Distribution - All Tweets',
            align: "left",
            offsetX: 10,
            fontFamily: "Open Sans",
            fontSize: 25
        },
        plotarea: {
            margin: "20 0 0 0"
        },
        series: [
            {
                values: [negativeCount],
                text: "Negative",
                backgroundColor: '#FF7965'
            },
            {
                values: [neutralCount],
                text: "Neutral",
                backgroundColor: '#FFCB45'
            },
            {
                values: [positiveCount],
                text: "Positive",
                backgroundColor: '#6FB07F'
            }
        ]
    };

    zingchart.render({
        id: "pieChart",
        data: myPieConfig,
        height: '100%',
        width: '100%'
    });

}

function drawEntitySentimentChart(bar_object) {

    var myConfig = {
        type: "bar",
        stacked: true,
        title: {
            fontColor: "#8e99a9",
            text: 'Sentiment Distribution - Per Entity',
            align: "left",
            offsetX: 10,
            fontFamily: "Open Sans",
            fontSize: 25,
            "adjust-layout": true
        },
        legend: {
            toggleAction: 'remove',
            "adjust-layout": true
        },
        scaleX: {
            labels: bar_object['entity_names'] //['brand', 'tv shows', 'person']
        },
        plot: {
            valueBox: {
                text: "Total Tweet: %stack-total",
                backgroundColor: 'black',
                rules: [
                    {
                        rule: '%stack-top == 0',
                        visible: 0
                    }
                ]
            },
            "adjust-layout": true,
            animation: {
                effect: 2,
                method: 5,
                speed: 900,
                sequence: 1,
                delay: 3000
            }
        },
        series: [
            {
                text: 'positive',
                values: bar_object['positive_counts'],//[135, 42, 67],
                stack: 1
            },
            {
                text: 'negative',
                values: bar_object['negative_counts'],//[10, 15, 10],
                stack: 1
            },
            {
                text: 'neutral',
                values: bar_object['neutral_counts'],//[25, 45, 25],
                stack: 1
            }
        ]
    };
    zingchart.render({
        id: 'barChart',
        data: myConfig,
        height: '100%',
        width: '100%'
    });

}

function myScroll() {
    let target = document.getElementById("pieChart")

    //scroll to specific div when go to button is clicked
    var scrollContainer = target;
    do { //find scroll container
        scrollContainer = scrollContainer.parentNode;
        if (!scrollContainer) return;
        scrollContainer.scrollTop += 1;
    } while (scrollContainer.scrollTop == 0);

    var targetY = 0;
    do { //find the top of target relatively to the container
        if (target == scrollContainer) break;
        targetY += target.offsetTop;
    } while (target = target.offsetParent);

    scroll = function (c, a, b, i) {
        i++;
        if (i > 30) return;
        c.scrollTop = a + (b - a) / 30 * i;
        setTimeout(function () {
            scroll(c, a, b, i);
        }, 20);
    }
    // start scrolling
    scroll(scrollContainer, scrollContainer.scrollTop, targetY, 0);
}