from deepface import DeepFace
image_path = r"C:\Users\admin\OneDrive\Pictures\test_image.jpg"

result = DeepFace.analyze(img_path=image_path, actions=['emotion'])

print(result)
