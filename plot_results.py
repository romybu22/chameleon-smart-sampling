import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

smart_sampling_csv = "C:\\Users\\operi157093\\Desktop\\Master\\RecSys_project\\smart_sampling_eval_stats_benchmarks.csv"
chameleon_with_benchmarks_csv = "C:\\Users\\operi157093\\Desktop\\Master\\RecSys_project\\CHAMELEON results\\results\\results\\eval_stats_benchmarks.csv"

smart_sampling = pd.read_csv(smart_sampling_csv)
chameleon_with_benchmarks = pd.read_csv(chameleon_with_benchmarks_csv)

benchmarks = ['CHAMELEON', 'Pop Recent', 'Co-ocurrent', 'Item-KNN', 'V-SkNN', 'Content-Based', 'Seequential Rules', 'Smart Sampling']


def plot_graph_data(attr):
    attr_columns = [column for column in list(chameleon_with_benchmarks.columns) if attr in column][1:8]
    data = [(benchmarks[i], chameleon_with_benchmarks[[attr_columns[i]]].values) for i in range(len(attr_columns))]
    data.append((benchmarks[len(benchmarks) - 1], smart_sampling.hitrate_at_n.values if attr is 'hitrate' else smart_sampling.mrr_at_n.values))
    data.sort(reverse=True, key=lambda tup: np.mean(tup[1]))

    [plt.plot(datum[1], label=f"{datum[0]}") for datum in data]

    plt.xlabel('Hour')
    plt.ylabel('HR@5' if attr is 'hitrate' else 'MRR@5')
    plt.legend(loc='best')
    plt.show()


def plot_box_data(attr):
    attr_columns = [column for column in list(chameleon_with_benchmarks.columns) if attr in column][1:8]

    data = [(benchmarks[i], chameleon_with_benchmarks[[attr_columns[i]]].values) for i in range(len(attr_columns))]
    data.append((benchmarks[len(benchmarks) - 1], smart_sampling.hitrate_at_n.values if attr is 'hitrate' else smart_sampling.mrr_at_n.values))
    data.sort(reverse=True, key=lambda tup: np.mean(tup[1]))

    label = "Benchmarks"
    value = 'HR@5' if attr is 'hitrate' else 'MRR@5'
    data_dict = {label: [], value: []}

    for datum in data:
        curr_benchmark = datum[0]
        curr_benchmark_values = datum[1]
        curr_benchmark_values = np.reshape(curr_benchmark_values, -1)

        for val in curr_benchmark_values:
            data_dict[label].append(curr_benchmark)
            data_dict[value].append(val)

    df = pd.DataFrame(data_dict)

    values_by_labels = df.groupby([label],sort=False)[value]
    medians = values_by_labels.median()
    median_labels = [str(np.round(s, 2)) for s in medians]

    plt.figure(figsize=(15, 10))
    box_plot = sns.boxplot(x=label, y=value, data= df)

    #Add text on top of plot
    pos = range(len(benchmarks))
    for tick,label in zip(pos,box_plot.get_xticklabels()):
        #Add median
        box_plot.text(tick, medians[tick] + 0.005, median_labels[tick],
                horizontalalignment='center', size='small', color='black', weight='bold')

    plt.show()


plot_graph_data('hitrate')
plot_graph_data('mrr')

plot_box_data('hitrate')
plot_box_data('mrr')


#print(smart_sampling.head())