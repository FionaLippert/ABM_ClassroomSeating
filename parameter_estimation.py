from model import *
from social import network
from data_processing import process_form
import model_comparison
import run_model
import matplotlib.pyplot as plt
import numpy as np
from noisyopt import minimizeSPSA
import time
from os import path
import json

MODEL_DATA_PATH = "model_output/parameter_estimation"
FILE_NAME = time.strftime("%Y%m%d-%H%M%S") + ".json"

RESULTS_JSON = []


"""
Compute the value of the objective function for parameter estimation.
Several seating processes with different random seeds are simulated and the output patterns are compared to the desired output.

Args:
    coefs: coefficients for the utility function
    class_size: total number of students to be included into the social network
    num_iterations: number of students that enter the classroom
    target_output: binary matrix representing the desired seating distribution
    method: {'lbp', 'cluster', 'entropy'} The method to be used to compute the profiles of the seating distributions

Returns:
    mean_error: mean MSE between model output profiles and target output profiles
"""
def objective_function(coefs, class_size, num_iterations, num_repetitions, target_output, method):

    # assure that the coefficients sum up to one
    coefs = [(c/sum(coefs) if sum(coefs) > 0 else 0) for c in coefs]
    print("###########################################################################")
    print("run the model with coefficients [{:.4f} {:.4f} {:.4f} {:.4f}]".format(coefs[0],coefs[1],coefs[2],coefs[3]))

    # run the model several times to handle stochasticity
    model_outputs = []
    errors = []
    for seed in range(num_repetitions):
        print("repetition {}".format(seed + 1))
        model = run_model.init_default_model(coefs, class_size, seed)
        for n in range(num_iterations):
            model.step()
        model_output = model.get_binary_model_state()
        model_outputs.append(model_output)

        # compute the error between model output and target output
        aisles_x = model.classroom.aisles_x
        errors.append(model_comparison.compare(model_output, target_output, method=method, aisles=aisles_x))

    # compute the error averaged over the set of runs
    mean_error = np.mean(errors)
    print("mean error = {:.4f}".format(mean_error))

    # save the results
    RESULTS_JSON.append({"coefs":coefs, "errors":errors})

    return mean_error


"""
Save the results from repeated simulation with given coefficients as a json file_name.
All results collected from one parameter estimation process are included into the same file.
"""
def save_json():

    with open(path.join(MODEL_DATA_PATH, FILE_NAME), mode='w', encoding='utf-8') as f:
        json.dump(RESULTS_JSON, f)


"""
Create a dummy seating distribution

Args:
    width: horizontal number of seats
    height: vertical number of seats
    num_iterations: number of Students

Returns:
    output: binary (width x height)-matrix
"""
def create_random_test_output(width, height, num_iterations):

    output = np.zeros((width,height))
    output[:num_iterations] = 1
    np.random.shuffle(output)

    return output


if __name__ == "__main__":

    """
    run the parameter estimation
    """

    class_size = 200 # a social network with 200 students is used
    num_iterations = 25 # 25 students are sampled from this network and enter the classroom one by one

    target_output = create_random_test_output(20, 13, num_iterations) # dummpy seating distribution for comparison
    method = 'lbp' # the method used for comparison
    num_repetitions = 10 # number of runs with different random seeds per parameter combination

    # bounds for the parameters to be estimated
    bounds = [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0], [0.0, 1.0]]

    # initial guess
    x0 = np.array([0.25, 0.25, 0.25, 0.25])

    # simultaneous perturbation stochastic approximation algorithm
    result = minimizeSPSA(objective_function, x0,
            args=(class_size, num_iterations, num_repetitions, target_output, method),
            bounds=bounds, niter=10, a=0.1, paired=False)

    save_json()

    print(result)