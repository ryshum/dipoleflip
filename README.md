# dipoleflip
_dipoleflip_ is an algorithm that allows us to resolve the issue of sign-ambiguity in source-reconstructed data. Based on the idea that subjects roughly share similar physiological features, our algorithm relies on the
assumption that the lagged partial correlation between each pair of brain regions (channels)
has the same sign across subjects.

## Getting Started
### Method 1. Running Jupyter Notebooks
#### 1. Clone Repository
You can clone the repository via:

```
git clone https://github.com/ryshum/dipoleflip
```
#### 2. Setting up a conda environment 

Four packages are required to run the notebooks: `numpy`, `pandas`, `scipy` and `jupyter-lab`.


A ```requirements.txt``` file has been provided with all the essential packages required. This file can be used
to set up a new conda environment (pip not possible yet) which allows you to run the jupyter notebooks.

To set up a new conda environment called "test", type in the following command in your terminal:

```conda create -c conda-forge --name test --file requirements.txt```

The command will create a new conda environment called 'test' with all the packages installed. Activate it by:

```conda activate test```

You can now launch jupyter notebooks using the command in terminal:

```jupyter lab```


### Method 2. Running the pypi package (in progress)
Once the package is published to pypi, you'd be able to install it via:

```
pip install dipoleflip
```


## Authors

* **Ryshum Ali** - *Initial work* - [ryshum](https://github.com/ryshum)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

