from typing import final
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import AmazonImageVerifyForm,FlipcartImageVerifyForm, UserRegisterForm, UserUpdateForm
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
import os,cv2,qrcode,time,uuid
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



# Create your views here.
def home(request):
    return render(request, 'users/home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect(reverse('home'))
    
    if request.method == "POST":
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            subject = "Welcome to E-Recycler"
            message = f'Hi {user.username},Thankyou for registering in our platform.'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email, ]
            

            send_mail( subject, message, email_from, recipient_list )
   

            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'],
                                    )

            login(request, new_user)
            return redirect('home')
        else:
            messages.warning(request,'Oops! some error occured, try agin.')
    
    else:
        form = UserRegisterForm()
    
    return render(request, 'users/register.html',{'form':form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile') # we are redirecting for a get request, if we refresh
        else:
            messages.warning(request,'Some error occured, please try again later.')

    else:
        u_form = UserUpdateForm(instance=request.user)

    context = {
        'u_form': u_form,
    }

    return render(request, 'users/profile.html', context)

def VerificationSlots(request):
    return render(request, 'users/verificationslots.html')

def AImageVerify(request):
    if request.method == 'POST':
        form = AmazonImageVerifyForm(request.POST, request.FILES)

        if form.is_valid():
            name = form.save(commit=False)
            name.user = request.user
            name.save()
            img = str(form.cleaned_data.get('a_image'))
            print(img)
            inpt = './media/amazon_images/'+img
            # Load the model
            model = load_model('./keras_model.h5')

            # Create the array of the right shape to feed into the keras model
            # The 'length' or number of images you can put into the array is
            # determined by the first position in the shape tuple, in this case 1.
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
            # Replace this with the path to your image
            image = Image.open(inpt).convert('RGB')
            #resize the image to a 224x224 with the same strategy as in TM2:
            #resizing the image to be at least 224x224 and then cropping from the center
            size = (224, 224)
            image = ImageOps.fit(image, size, Image.ANTIALIAS)

            #turn the image into a numpy array
            image_array = np.asarray(image)
            # Normalize the image
            normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
            # Load the image into the array
            data[0] = normalized_image_array

            # run the inference
            prediction = model.predict(data)[0]
            predicted_class = None

            second_check = os.listdir("./media/amazon_images")

            for i in second_check:
                splt = os.path.splitext(i)
                ck = splt[0][0:-8]+splt[1]
                print(ck)

           
            if img in ck:
                predicted_class = "This photo was already uploaded"
                os.remove("./media/amazon_images/"+img)
                messages.warning(request,f'{predicted_class}')
                return redirect(reverse('amazon-verify'))

            elif prediction[0]>prediction[1]:
                unid = str(uuid.uuid4())[:8]
                source = inpt
                rename_file = os.path.splitext(source)
                new_name = rename_file[0]+unid+rename_file[1] 
                dest = new_name
                os.rename(source,dest)
                predicted_class = "Uploaded image was verified as 'AMAZON' "
        
                qr = qrcode.QRCode(version = 1 , box_size=15 , border=5)

                cat = "Amazon"

                data =  f"""
                Name: {request.user.username} 

                Image-Name: {img} 

                category: {cat}

                id: {unid}
                
                """
                #data = "whatsapp://send?phone=+916369613398"
                qr.add_data(data)
                qr.make (fit = True) ## makes the size changable
                imge = qr.make_image(fill = 'black' , back_color= 'white' )## making the qr code
                pth = f"./qrcodes/amazon/{request.user.username}{unid}.png"
                imge.save(pth)

                image1=cv2.imread(dest)
                image2=cv2.imread(pth)

                sze = tuple(image1.shape[1::-1])

                image1=cv2.resize(image1,sze)
                image2=cv2.resize(image2,sze)

                final_img =np.hstack([image1,image2])
                f_out = f"./final_output/amazon/{request.user.username}{unid}"+".png"
                sve = cv2.imwrite(f_out,final_img)

                subject = "Image verification successful (E-recycler)"
                body = f"The {img} you uploaded was verified successfully. Our guy will be collecting the box from you asap! and once the verification is done. The verification will be done with the help of the qrcode attached."
                sender_email = "ab7710850@gmail.com"
                receiver_email = request.user.email

                # Create a multipart message and set headers
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = receiver_email
                message["Subject"] = subject
                message["Bcc"] = receiver_email  # Recommended for mass emails

                # Add body to email
                message.attach(MIMEText(body, "plain"))

                filename = f_out  # In same directory as script

                # Open PDF file in binary mode
                with open(filename, "rb") as attachment:
                    # Add file as application/octet-stream
                    # Email client can usually download this automatically as attachment
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                # Encode file in ASCII characters to send by email
                #If the sender's or recipient's email address contains non-ASCII characters, 
                #sending of a message requires also 
                #encoding of these to a format that can be understood by mail servers. 

                encoders.encode_base64(part)

                # Add header as key/value pair to attachment part
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )

                # Add attachment to message and convert message to string
                message.attach(part)
                text = message.as_string()

                # Log in to server using secure context and send email
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender_email, 'grfbsxqyymukecvg')
                    server.sendmail(sender_email, receiver_email, text)

              
            else:
                predicted_class = "No, this image is not verified as 'AMAZON' "
                os.remove(inpt)
            print(prediction)
            messages.success(request,f'{predicted_class}')
            return redirect(reverse('amazon-verify'))
    else:
        form = AmazonImageVerifyForm()

    return render(request, 'users/aimageverify.html', {'form':form})


def FImageVerify(request):
    if request.method == 'POST':
        form = FlipcartImageVerifyForm(request.POST, request.FILES)

        if form.is_valid():
            name = form.save(commit=False)
            name.user = request.user
            name.save()
            img = str(form.cleaned_data.get('f_image'))
            print(img)
            inpt = './media/flipcart_images/'+img
            # Load the model
            model = load_model('./keras_model.h5')

            # Create the array of the right shape to feed into the keras model
            # The 'length' or number of images you can put into the array is
            # determined by the first position in the shape tuple, in this case 1.
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
            # Replace this with the path to your image
            image = Image.open(inpt).convert('RGB')
            #resize the image to a 224x224 with the same strategy as in TM2:
            #resizing the image to be at least 224x224 and then cropping from the center
            size = (224, 224)
            image = ImageOps.fit(image, size, Image.ANTIALIAS)

            #turn the image into a numpy array
            image_array = np.asarray(image)
            # Normalize the image
            normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
            # Load the image into the array
            data[0] = normalized_image_array

            # run the inference
            prediction = model.predict(data)[0]
            predicted_class = None
            second_check = os.listdir("./media/flipcart_images")

            for i in second_check:
                splt = os.path.splitext(i)
                ck = splt[0][0:-8]+splt[1]
                print(ck)

           
            if img in ck:
                predicted_class = "This photo was already uploaded"
                os.remove("./media/flipcart_images/"+img)
                messages.warning(request,f'{predicted_class}')
                return redirect(reverse('flipcart-verify'))

            elif prediction[0]<prediction[1]:
                unid = str(uuid.uuid4())[:8]
                source = inpt
                rename_file = os.path.splitext(source)
                new_name = rename_file[0]+unid+rename_file[1] 
                dest = new_name
                os.rename(source,dest)
                predicted_class = "Uploaded image was verified as 'FLIPKART' "
        
                qr = qrcode.QRCode(version = 1 , box_size=15 , border=5)
                
                cat = "Flipkart"

                data =  f"""
                Name: {request.user.username} 

                Image-Name: {img} 

                Category: {cat}

                id: {unid}
                
                """
                #data = "whatsapp://send?phone=+916369613398"
                qr.add_data(data)
                qr.make (fit = True) ## makes the size changable
                imge = qr.make_image(fill = 'black' , back_color= 'white' )## making the qr code
                pth = f"./qrcodes/flipcart/{request.user.username}{unid}.png"
                imge.save(pth)

                image1=cv2.imread(dest)
                image2=cv2.imread(pth)

                sze = tuple(image1.shape[1::-1])

                image1=cv2.resize(image1,sze)
                image2=cv2.resize(image2,sze)

                final_img =np.hstack([image1,image2])
                f_out = f"./final_output/flipcart/{request.user.username}{unid}"+".png"
                sve = cv2.imwrite(f_out,final_img)

                subject = "Image verification successful (E-recycler)"
                body = f"The {img} you uploaded was verified successfully. Our guy will be collecting the box from you asap! and once the verification is done. The verification will be done with the help of the qrcode attached."
                sender_email = "ab7710850@gmail.com"
                receiver_email = request.user.email

                # Create a multipart message and set headers
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = receiver_email
                message["Subject"] = subject
                message["Bcc"] = receiver_email  # Recommended for mass emails

                # Add body to email
                message.attach(MIMEText(body, "plain"))

                filename = f_out  # In same directory as script

                # Open PDF file in binary mode
                with open(filename, "rb") as attachment:
                    # Add file as application/octet-stream
                    # Email client can usually download this automatically as attachment
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                # Encode file in ASCII characters to send by email
                #If the sender's or recipient's email address contains non-ASCII characters, 
                #sending of a message requires also 
                #encoding of these to a format that can be understood by mail servers. 

                encoders.encode_base64(part)

                # Add header as key/value pair to attachment part
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )

                # Add attachment to message and convert message to string
                message.attach(part)
                text = message.as_string()

                # Log in to server using secure context and send email
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender_email, 'grfbsxqyymukecvg')
                    server.sendmail(sender_email, receiver_email, text)
            else:
                predicted_class = "No, this image is not verified as 'FLIPKART'"
                os.remove(inpt)

            print(prediction)
            messages.success(request,f'{predicted_class}')
            
            return redirect(reverse('flipcart-verify'))
    else:
        form = FlipcartImageVerifyForm()

    return render(request, 'users/fimageverify.html', {'form':form})

@login_required
def user_logout(request):
    time.sleep(2) # waiting for 2 sec
    logout(request) # using django.contrib.auth.logout(), It takes an HttpRequest object and has no return value
    messages.success(request,f'You are logged out successfully') # logout success msg
    return redirect('login') # redirect to login page


