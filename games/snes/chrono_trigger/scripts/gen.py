from gen_script import generate_full_script
from gen_dict import generate_dict
#from gen_audio import generate_audio

if __name__ == "__main__":
    categories_file_path = '../categories.csv'
    full_script_path = '../full_script.csv'
    dict_path = '../dict.json'
    audio_output_path = '../audio'
    
    # Generate full script
    print('Generating full script...')
    generate_full_script(categories_file_path, full_script_path)
    print('Full script generated.')
    
    # Generate dictionary
    print('Generating dictionary...')
    generate_dict(full_script_path, dict_path)
    print('Dictionary generated.')
    
    # Generate audio
    print('Generating audio...')
    #generate_audio(full_script_path, audio_output_path)
    print('Audio generated.')
    
