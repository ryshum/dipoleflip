import numpy as np
import matplotlib.pyplot as plt
plt.rc('font',family='Arial', size=14)

def create_plots(score_path, accuracy_path, low_power_solution):
    """
    This function creates 2 types of plots for the solution obtained for the specified dataset:
    1. A Score Vs. Iterations plot
    2. An Accuracy Vs. Iteration plot (for normal method and not hierarchical)

    :param score_path: List with all the scores in each cycle per each run
    :param accuracy_path: List with all the accuracies in each cycle per each run
    :param low_power_solution: Boolean suggesting whether the solution was Hierarchical or not - default = False
    """
    if low_power_solution is False: # * we run the Normal method of flips computation
        no_runs = len(accuracy_path)
        scores = score_path
        accuracies = accuracy_path

        # * compute iterations or cycles in each run
        iterations = np.empty(no_runs)
        for run in range(no_runs):
            iterations_per_run = len(scores[run])
            iterations[run] = iterations_per_run

        # Colors - as many as the number of runs
        hex_colors = ["#FFA500", '#00CED1', '#A52A2A', '#008000', '#800080']

        # * Plotting iterations vs score for all runs -------------------------------------------------
        fig, ax1 = plt.subplots()
        for i, (iters, sc, color) in enumerate(zip(iterations, scores, hex_colors)):
            x_coordinates = range(1, int(iters)+1)
            ax1.plot(x_coordinates, sc, label=f'Run {i + 1}', color=color, linestyle='-', markersize=5)

        ax1.set_xlabel('Iterations', fontsize=14)
        ax1.set_ylabel('Score', fontsize=14)
        ax1.legend(loc='upper left')
        ax1.legend(prop=dict(size=10))
        ax1.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax1.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
        ax1.minorticks_on()
        ax1.set_title('Iterations vs. Score for All Runs', fontweight='bold')
        ax1.set_facecolor('none')

        # Save the first plot
        fig.savefig('iter_vs_score.png', transparent=True)
        plt.show()

        # * Plotting iterations vs accuracy for all runs -------------------------------------------------
        fig, ax2 = plt.subplots()
        for i, (iters, acc, color) in enumerate(zip(iterations, accuracies, hex_colors)):
            x_coordinates = range(1, int(iters) + 1)
            ax2.plot(x_coordinates, acc, label=f'Run {i + 1}', color=color, linestyle='-', markersize=5)

        ax2.set_xlabel('Iterations')
        ax2.set_ylabel('Accuracy')
        ax2.legend(loc='lower right')
        ax2.legend(prop=dict(size=10))
        ax2.grid(which='major', color='#DDDDDD', linewidth=0.8)
        ax2.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
        ax2.minorticks_on()
        ax2.set_title('Iterations vs. Accuracy for All Runs', fontweight='bold')
        ax2.set_facecolor('none')

        # Save the second plot
        fig.savefig('iter_vs_acc.png', transparent=True)
        plt.show()


    # if we want to plot for the hierarchical solution
    else:
        no_of_levels = len(score_path)

        for level in range(no_of_levels):
            no_of_groups = len(score_path[level])
            max_score_runs = {}

            # find for each group the run with the maximum score reached
            for groups in range(no_of_groups):
                all_runs_scores = score_path[level][groups]
                # initialize variables to store the maximum value and its index
                max_value = -np.inf
                max_index = -1

                # iterate through the list to find the maximum value and its index
                for i, array in enumerate(all_runs_scores):
                    local_max = array.max()
                    if local_max > max_value:
                        max_value = local_max
                        max_index = i

                max_score_runs[groups] = all_runs_scores[max_index]

            # plotting
            fig, ax1 = plt.subplots()
            group = 0
            for result in max_score_runs:
                max_score_run = max_score_runs[result]
                print(f'Group {result}: Best Run {max_score_run}')

                iters = np.arange(1, len(max_score_run) + 1)

                ax1.plot(iters, max_score_run, label=f'Group {group + 1}', marker='o', linestyle='-',
                         markersize=5)

                ax1.set_xlabel('Iterations')
                ax1.set_ylabel('Score')
                ax1.legend(loc='upper left')
                ax1.legend(prop=dict(size=10))
                ax1.grid(which='major', color='#DDDDDD', linewidth=0.8)
                ax1.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
                ax1.set_title('Iterations vs Score for best run for each group', fontweight='bold')
                ax1.set_facecolor('none')

                group = group + 1

            fname = 'iter_vs_score_hier_level_' + str(level) + '.png'
            fig.savefig(fname=fname, transparent=True)
            plt.show()






