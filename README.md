# res2dmod_filehandler

Simple python script to read and write res2dmod 
electrode configuration files.

```python
if __name__ == '__main__':

    # Test function used for filtering
    def is_config_ok(configuration:Configuration):
        if configuration.xc2==720:
            return True
        else:
            #print(f"skipping Configuration {item.id}")
            pass
        return False


    #read file
    config_model=ForwardModellingConfigurations.import_file('GD_1176.txt')
    print(f'Imported {len(config_model.all_configurations)} configurations')

    #filter
    new_list=[]
    for item in config_model.all_configurations:
        if is_config_ok(item):
            new_list.append(item)
    config_model.all_configurations= new_list

    #export new file
    config_model.export(f'GD_1176_modified_to_{len(config_model.all_configurations)}.txt')
    print(f'Exported {len(config_model.all_configurations)} configurations')
```

