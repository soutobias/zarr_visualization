"""_summary_
"""
import os
from tempfile import NamedTemporaryFile
import numpy as np
import xarray as xr
import urllib3
from dotenv import load_dotenv
import s3fs
import ipywidgets as widgets
from ipyleaflet import Map, basemaps
from localtileserver import get_leaflet_tile_layer, TileClient

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ZarrVisualization():
    """_summary_
    """

    def __init__(self, bucket_name='tobfer') -> None:
        self.bucket_name = bucket_name
        self.remote_options = {
            "anon": False,
            "key":os.environ.get('aws_access_key_id'),
            "secret": os.environ.get('aws_secret_access_key'),
            "endpoint_url": os.environ.get('endpoint_url')
        }
        self.fs = s3fs.S3FileSystem(**self.remote_options)

        self.list_of_variables = [item.split('/')[-1] for item in self.fs.ls(bucket_name)]
        self.limits = [0,0,0,0,0]
        self.create_first_widgets()
        self.m = Map(center=[40, 0],
                     zoom=3,
                     basemap=basemaps.CartoDB.DarkMatter,
                     interpolation='nearest')
        self.ds = None
        self.data_path = None

    def create_first_widgets(self):
        """_summary_
        """
        self.variable_select = widgets.Dropdown(
            options=self.list_of_variables,
            value=self.list_of_variables[0],
            description='Variable:'
        )
        self.open_button = widgets.Button(description="Open Zarr")
        self.sel_button = widgets.HBox()
        self.show_data = widgets.HBox()

        self.lat_min_container = widgets.HBox()
        self.lat_max_container = widgets.HBox()
        self.lon_min_container = widgets.HBox()
        self.lon_max_container = widgets.HBox()
        self.printed_data_path = widgets.HBox()
        self.data_information = widgets.HBox()
        self.time_counter_container = widgets.HBox()

        self.loading_spinner = widgets.HTML(value="Loading...")
        self.loading_container = widgets.VBox()


    def plot_data(self):
        """_summary_
        """
        self.loading_container.children = [self.loading_spinner]

        temp_file = NamedTemporaryFile(suffix='.tif', delete=False)
        self.ds.rio.to_raster(temp_file.name)
        temp_file.close()
        client = TileClient(temp_file.name)
        t = get_leaflet_tile_layer(source=client, colormap='RdYlBu_r')
        self.m.add(t)
        self.loading_container.children = []


    def sel_zarr_data(self):
        """_summary_
        """
        self.loading_container.children = [self.loading_spinner]
        self.ds = self.ds.sel(y=slice(self.limits[0], self.limits[1]))
        self.ds = self.ds.sel(x=slice(self.limits[2], self.limits[3]))
        if len(self.limits) == 5:
            self.ds = self.ds.sel(time_counter=self.limits[4])
        self.ds.attrs['scale_factor'] = 1.0
        self.ds.attrs['add_offset'] = 0.0
        self.ds = self.ds.assign_coords(band=1)
        self.ds = self.ds.drop_vars(['nav_lat', 'nav_lon'])
        self.data_information.children = [widgets.Output()]
        with self.data_information.children[0]:
            print(self.ds)

        self.loading_container.children = []
        self.show_data.children = [widgets.Button(description="Plot Data")]
        self.show_data.children[0].on_click(lambda b: self.plot_data())

    def open_zarr_file(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        ds = xr.open_zarr(self.data_path)
        nav_lat = ds.nav_lat.values
        new_y = np.linspace(nav_lat.min(), nav_lat.max(), num=nav_lat.shape[0])
        nav_lon = ds.nav_lon.values
        # new_x = np.linspace(nav_lon.min(), nav_lon.max(), num=nav_lon.shape[1])
        new_x = nav_lon[1000]
        ds = ds.assign_coords(y=new_y, x=new_x)
        ds = ds.sortby('x')
        ds = ds.sortby('y')
        if "x" not in ds.dims and "y" not in ds.dims:
            latitude_var_name = "lat"
            longitude_var_name = "lon"
            if "latitude" in ds.dims:
                latitude_var_name = "latitude"
            if "longitude" in ds.dims:
                longitude_var_name = "longitude"
            ds = ds.rename({latitude_var_name: "y", longitude_var_name: "x"})
        if "time_counter" in ds.dims:
            ds = ds.transpose("time_counter", "y", "x")
        else:
            ds = ds.transpose("y", "x")
        if (ds.x > 180).any():
            ds = ds.assign_coords(x=(ds.x + 180) % 360 - 180)
            ds = ds.sortby(ds.x)
        crs = ds.rio.crs or "epsg:4326"
        ds.rio.write_crs(crs, inplace=True)
        return ds

    def update_limits(self, change):
        """_summary_

        Args:
            change (_type_): _description_
        """
        self.limits[0] = self.lat_min_container.children[0].value
        self.limits[1] = self.lat_max_container.children[0].value
        self.limits[2] = self.lon_min_container.children[0].value
        self.limits[3] = self.lon_max_container.children[0].value
        if len(self.limits) == 5:
            self.limits[4] = self.time_counter_container.children[0].value

    def process_zarr_file(self, subdata_select):
        """_summary_
        """
        self.loading_container.children = [self.loading_spinner]

        self.data_path = f"{self.remote_options['endpoint_url']}{self.bucket_name}/{self.variable_select.value}/{subdata_select.value}"
        print(self.data_path)

        self.ds = self.open_zarr_file()
        self.ds = self.ds[subdata_select.value[:-5]]
        self.lat_min_container.children = [
            widgets.FloatSlider(
                value=40,
                min=-89,
                max=89,
                description='Min Lat:',
                continuous_update=False
            )
        ]

        self.lat_max_container.children = [widgets.FloatSlider(
            value=60,
            min=-89,
            max=89,
            description='Max Lat:',
            continuous_update=False
        )]
        self.lon_min_container.children = [widgets.FloatSlider(
            value=-54,
            min=-179,
            max=179,
            description='Min Lon:',
            continuous_update=False
        )]

        self.lon_max_container.children = [widgets.FloatSlider(
            value=-37,
            min=-179,
            max=179,
            description='Max Lon:',
            continuous_update=False
        )]

        if 'time_counter' in list(self.ds.coords):
            time_values = self.ds.time_counter.values
            self.time_counter_container.children = [
                widgets.Dropdown(
                    options=time_values,
                    value= time_values[0],
                    description='Time Counter:'
                )
            ]
            self.time_counter_container.children[0].observe(self.update_limits, names='value')
        self.update_limits('')
        self.lat_min_container.children[0].observe(self.update_limits, names='value')
        self.lat_max_container.children[0].observe(self.update_limits, names='value')
        self.lon_min_container.children[0].observe(self.update_limits, names='value')
        self.lon_max_container.children[0].observe(self.update_limits, names='value')

        self.loading_container.children = []
        self.sel_button.children = [widgets.Button(description="Clip Data")]
        self.sel_button.children[0].on_click(lambda b: self.sel_zarr_data())


    def update_data_path(self, change):
        """_summary_

        Args:
            change (_type_): _description_
        """
        self.data_path.children = [widgets.Output()]
        with self.data_path.children[0]:
            print(f"{self.remote_options['endpoint_url']}{self.bucket_name}/{self.variable_select.value}/{change['new']}")
