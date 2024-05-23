# dipoleflip
_dipoleflip_ is an algorithm that allows us to resolve the issue of sign-ambiguity in source-reconstructed data. Based on the idea that subjects roughly share similar physiological features, our algorithm relies on the
assumption that the lagged partial correlation between each pair of brain regions (channels)
has the same sign across subjects.

## Getting Started
### Prerequisites

What things you need to install the software and how to install them

- numpy, pandas, scipy
```
pip install numpy
pip install pandas
pip install scipy
```

### Installing
You can clone the repository via:

```
git clone https://github.com/ryshum/dipoleflip
```

Once the package is published to pypi, you'd be able to install it via:

```
pip install dipoleflip
```



## Running the tests

The program assumes that your data folder is located in the same directory as the scripts.
To run the algorithm, the following command can be used in 
command line:

```
python initiate_flips.py modulename.functionname no_of_subjects no_of_channels method_for_computation

% Examples
python initiate_flips.py grid_search.grid_search 10 10 Hierarchical
python initiate_flips.py grid_search.grid_search 25 10 Normal
```

## Authors

* **Ryshum Ali** - *Initial work* - [ryshum](https://github.com/ryshum)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
